import importlib.util
import os
import signal
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "service_audit.py"
SPEC = importlib.util.spec_from_file_location("service_audit", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


@pytest.fixture
def owner(tmp_path):
    return audit.Process(12345, os.getuid(), 1, "started", tmp_path, "python", False)


def test_parse_ss_handles_shared_pids_ipv6_zone_and_duplicates():
    line = 'LISTEN 0 10 [::ffff:127.0.0.1]:8090 *:* users:(("python",pid=8,fd=3),("python",pid=9,fd=3))'
    assert audit.parse_listeners("tcp", line + "\n" + line) == [
        audit.Listener("tcp", "::ffff:127.0.0.1", 8090, (8, 9))
    ]
    assert audit.parse_listeners("udp", "UNCONN 0 0 [fe80::1]%eth0:546 *:*")[0].host == "fe80::1%eth0"


@pytest.mark.parametrize("host,listener,expected", [
    ("127.0.0.1", "::ffff:127.0.0.1", True),
    ("127.0.0.1", "127.0.0.2", False),
    ("127.0.0.1", "0.0.0.0", True),
])
def test_socket_address_matching(host, listener, expected):
    assert audit.address_matches(host, listener) is expected


def test_invalid_stackctl_output_is_not_treated_as_empty_services(tmp_path):
    with pytest.raises(ValueError, match="erwarteten Projekt"):
        audit.parse_services("demo", tmp_path, {"target": "local", "root": [], "services": []})


def test_project_failure_does_not_hide_other_project_services(tmp_path, monkeypatch):
    other = tmp_path / "other"

    def run(command, **kwargs):
        if kwargs["cwd"] == tmp_path:
            return subprocess.CompletedProcess(command, 1, "", "missing stack.services")
        return subprocess.CompletedProcess(command, 0, audit.json.dumps({
            "root": str(other), "target": "local", "services": [
                {"name": "api", "host": "localhost", "port": 8000, "status": "running",
                 "pid": 123, "managed": True},
            ],
        }), "")

    monkeypatch.setattr(subprocess, "run", run)
    services, errors = audit.inspect_services({"demo": tmp_path, "other": other})
    assert len(services) == 1 and services[0].project == "other"
    assert errors == {"demo": "missing stack.services"}


@pytest.mark.parametrize("status,managed", [("running", True), ("unhealthy", False)])
def test_cleanup_protects_healthy_and_external_services(owner, status, managed):
    service = audit.Service("demo", "api", "127.0.0.1", 8000, status, managed, owner.pid)
    listeners = [audit.Listener("tcp", "127.0.0.1", 8000, (owner.pid,))]
    allowed, _ = audit.cleanup_reason(owner, listeners, [service], {"demo": owner.cwd}, {})
    assert not allowed


def test_cleanup_does_not_kill_healthy_owner_on_shared_conflicting_port(owner):
    services = [
        audit.Service("demo", "api", "127.0.0.1", 8000, "running", True, owner.pid),
        audit.Service("other", "web", "127.0.0.1", 8000, "foreign", True, owner.pid),
    ]
    allowed, _ = audit.cleanup_reason(owner, [audit.Listener("tcp", "127.0.0.1", 8000, (owner.pid,))],
                                     services, {"demo": owner.cwd}, {})
    assert not allowed


@pytest.mark.parametrize("change,errors", [
    ({"cwd": Path("/outside")}, {}),
    ({"uid": -1}, {}),
    ({"supervised": True}, {}),
    ({}, {"demo": "cannot load config"}),
])
def test_cleanup_refuses_unsafe_or_unknown_owners(owner, change, errors):
    allowed, _ = audit.cleanup_reason(replace(owner, **change), [], [], {"demo": owner.cwd}, errors)
    assert not allowed


def test_cleanup_marks_unknown_project_listener_as_candidate_not_proven_hang(owner):
    allowed, reason = audit.cleanup_reason(owner, [], [], {"demo": owner.cwd}, {})
    assert allowed
    assert "Prüfkandidat" in reason


def test_preview_does_not_send_signal(owner, monkeypatch):
    monkeypatch.setattr(audit, "inspect_services", lambda paths: ([], {}))
    monkeypatch.setattr(audit, "inspect_listeners",
                        lambda: [audit.Listener("tcp", "127.0.0.1", 1234, (owner.pid,))])
    monkeypatch.setattr(audit, "inspect_process", lambda pid: owner)
    monkeypatch.setattr(audit, "terminate_selected",
                        lambda *args: pytest.fail("preview must not send signals"))
    assert audit.cleanup([owner.pid], False, {"demo": owner.cwd}, 1) == 0


def test_pid_identity_change_refuses_signal(owner, monkeypatch):
    monkeypatch.setattr(os, "pidfd_open", lambda pid: 7)
    monkeypatch.setattr(os, "close", lambda descriptor: None)
    monkeypatch.setattr(audit, "inspect_process", lambda pid: replace(owner, started="different"))
    monkeypatch.setattr(signal, "pidfd_send_signal", lambda *args: pytest.fail("PID identity changed"))
    with pytest.raises(ValueError, match="identität"):
        audit.terminate_selected(owner.pid, owner, 1, [])


@pytest.mark.parametrize("replacement_host", ["127.0.0.1", "0.0.0.0"])
def test_respawn_or_shared_socket_is_reported_as_not_freed(owner, monkeypatch, replacement_host):
    monkeypatch.setattr(os, "pidfd_open", lambda pid: 7)
    monkeypatch.setattr(os, "close", lambda descriptor: None)
    monkeypatch.setattr(audit, "inspect_process", lambda pid: owner)
    sent = []
    monkeypatch.setattr(signal, "pidfd_send_signal", lambda fd, sig: sent.append(sig))
    old = audit.Listener("tcp", "127.0.0.1", 1234, (owner.pid,))
    monkeypatch.setattr(audit, "inspect_listeners",
                        lambda: [replace(old, pids=(54321,), host=replacement_host)])
    with pytest.raises(ValueError, match="noch belegt"):
        audit.terminate_selected(owner.pid, owner, 0, [old])
    assert sent == [signal.SIGTERM]


def test_sigterm_releases_real_test_listener(tmp_path):
    child = subprocess.Popen(
        [sys.executable, "-u", "-c",
         "import socket,time; s=socket.socket(); s.bind(('127.0.0.1',0)); "
         "s.listen(); print(s.getsockname()[1],flush=True); time.sleep(30)"],
        cwd=tmp_path, stdout=subprocess.PIPE, text=True,
    )
    try:
        port = int(child.stdout.readline())
        process = audit.inspect_process(child.pid)
        listeners = audit.inspect_listeners()
        assert any(item.port == port and child.pid in item.pids for item in listeners)
        audit.terminate_selected(child.pid, process, 3, listeners)
        child.wait(timeout=3)
        assert child.returncode == -signal.SIGTERM
        assert not any(item.port == port for item in audit.inspect_listeners())
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=3)
        child.stdout.close()


@pytest.mark.parametrize("argv", [["--apply"], ["--wait", "nan"], ["--cleanup-pid", "1"]])
def test_cli_rejects_invalid_cleanup_arguments(argv):
    with pytest.raises(SystemExit) as exc:
        audit.main(argv)
    assert exc.value.code == 2
