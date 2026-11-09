#!/usr/bin/env python3
"""Inspect local ecosystem services and optionally terminate selected port owners."""

from __future__ import annotations

import argparse
import ipaddress
import json
import math
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from stackctl.spec import Project, SpecError, find_project


@dataclass(frozen=True)
class Service:
    project: str
    name: str
    host: str
    port: int
    status: str
    managed: bool
    pid: int | None


@dataclass(frozen=True)
class Listener:
    protocol: str
    host: str
    port: int
    pids: tuple[int, ...]


@dataclass(frozen=True)
class Process:
    pid: int
    uid: int
    parent: int
    started: str
    cwd: Path
    name: str
    supervised: bool


def project_paths(project: Project) -> dict[str, Path]:
    """Use stackctl's manifest and path-resolution rules, not its runtime registry."""
    return {project.root.name: project.root.resolve(), **{
        sibling.name: project.sibling_path(sibling).resolve()
        for sibling in project.siblings
    }}


def inspect_services(paths: dict[str, Path]) -> tuple[list[Service], dict[str, str]]:
    services: list[Service] = []
    errors: dict[str, str] = {}
    for name, root in paths.items():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "stackctl", "--target", "local", "--json", "status"],
                cwd=root, capture_output=True, text=True, timeout=45,
            )
            if result.returncode:
                raise ValueError(result.stderr.strip() or f"Exit-Code {result.returncode}")
            data = json.loads(result.stdout)
            services.extend(parse_services(name, root, data))
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            errors[name] = str(exc)
    return services, errors


def parse_services(name: str, root: Path, data: object) -> list[Service]:
    if not isinstance(data, dict) or data.get("target") != "local":
        raise ValueError("stackctl liefert keinen lokalen Status")
    if (not isinstance(data.get("root"), str) or Path(data["root"]).resolve() != root
            or not isinstance(data.get("services"), list)):
        raise ValueError("stackctl-Status gehört nicht zum erwarteten Projekt")
    services = []
    for item in data["services"]:
        if not isinstance(item, dict) or not all(key in item for key in (
            "name", "host", "port", "status", "managed", "pid",
        )):
            raise ValueError("Ungültiger Service im stackctl-Status")
        if (type(item["port"]) is not int or not 0 <= item["port"] <= 65535
                or type(item["managed"]) is not bool
                or any(not isinstance(item[key], str) for key in ("name", "host", "status"))
                or (item["pid"] is not None and type(item["pid"]) is not int)):
            raise ValueError("Ungültige Service-Feldtypen im stackctl-Status")
        services.append(Service(name, item["name"], item["host"], item["port"],
                                item["status"], item["managed"], item["pid"]))
    return services


def parse_listeners(protocol: str, output: str) -> list[Listener]:
    listeners = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) < 5:
            raise ValueError(f"Ungültige ss-Ausgabe: {line}")
        host, separator, port = fields[3].rpartition(":")
        if not separator or not port.isdigit():
            raise ValueError(f"Ungültige Socket-Adresse: {fields[3]}")
        listeners.append(Listener(protocol, host.replace("[", "").replace("]", ""), int(port),
                                  tuple(sorted({int(pid) for pid in re.findall(r"pid=(\d+)", line)}))))
    return list(dict.fromkeys(listeners))


def inspect_listeners() -> list[Listener]:
    listeners = []
    for protocol, option in (("tcp", "-ltnp"), ("udp", "-lunp")):
        result = subprocess.run(["ss", "-H", option], capture_output=True, text=True,
                                timeout=10, check=True)
        listeners.extend(parse_listeners(protocol, result.stdout))
    return listeners


def inspect_process(pid: int) -> Process:
    directory = Path(f"/proc/{pid}")
    fields = (directory / "stat").read_text().rsplit(")", 1)[1].split()
    cgroup = (directory / "cgroup").read_text()
    return Process(
        pid, directory.stat().st_uid, int(fields[1]), fields[19],
        (directory / "cwd").resolve(strict=True), (directory / "comm").read_text().strip(),
        any(line.rstrip().endswith(".service") for line in cgroup.splitlines())
        or supervisor_ancestor(int(fields[1])),
    )


def supervisor_ancestor(pid: int) -> bool:
    for _ in range(32):
        if pid <= 1:
            return False
        directory = Path(f"/proc/{pid}")
        if (directory / "comm").read_text().strip().startswith("supervisord"):
            return True
        fields = (directory / "stat").read_text().rsplit(")", 1)[1].split()
        pid = int(fields[1])
    raise ValueError("Prozessabstammung zu tief; Supervisor-Zuordnung unbekannt")


def address_matches(host: str, listener_host: str) -> bool:
    if host in {"", "*", "0.0.0.0", "::"} or listener_host in {"*", "0.0.0.0", "::"}:
        return True
    try:
        address = ipaddress.ip_address(listener_host.split("%", 1)[0])
        expected = ipaddress.ip_address("127.0.0.1" if host == "localhost" else host)
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        return address == expected
    except ValueError:
        return host == listener_host


def matching_services(listener: Listener, services: list[Service]) -> list[Service]:
    return [service for service in services if listener.protocol == "tcp"
            and service.port == listener.port and address_matches(service.host, listener.host)]


def cleanup_reason(process: Process, listeners: list[Listener], services: list[Service],
                   paths: dict[str, Path], errors: dict[str, str]) -> tuple[bool, str]:
    owned = [name for name, root in paths.items()
             if process.cwd == root or root in process.cwd.parents]
    if not owned:
        return False, "außerhalb der Manifestprojekte"
    if process.uid != os.getuid() or process.pid in {1, os.getpid(), os.getppid()}:
        return False, "fremder Benutzer oder geschützter Prozess"
    if any(name in errors for name in owned):
        return False, "Projektstatus unbekannt; Bereinigung gesperrt"
    if process.supervised:
        return False, "systemd-/Supervisor-Service; beim Prozessmanager stoppen"
    matching = [service for listener in listeners if process.pid in listener.pids
                for service in matching_services(listener, services)]
    if any(service.status == "running" or not service.managed for service in matching):
        return False, "gesunder oder extern/Compose-verwalteter Dienst"
    if any(service.pid == process.pid and service.status == "running" for service in services):
        return False, "gesunder Dienst ohne zugeordneten Listener"
    return True, "Prüfkandidat: unhealthy/foreign oder nicht in der aktiven Spec"


def print_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    widths = [max(len(row[index]) for row in [headers, *rows]) for index in range(len(headers))]
    for row in [headers, *rows]:
        print(" | ".join(value.ljust(width) for value, width in zip(row, widths)))


def report(paths: dict[str, Path], services: list[Service], errors: dict[str, str],
           listeners: list[Listener], all_ports: bool = False) -> None:
    print("LOKALE DIENSTE (aktive Projektkonfiguration; kein Remote-Cluster-Status)")
    print_table(("PROJEKT", "DIENST", "ADRESSE", "STACKCTL", "PID"), [
        (service.project, service.name, f"{service.host}:{service.port}", service.status,
         str(service.pid or "-")) for service in services
    ])
    for name, error in errors.items():
        print(f"FEHLER {name}: {error}", file=sys.stderr)
    print("\nTCP-/UDP-PORTBELEGUNG (fehlende PIDs: nicht sichtbar, nicht bereinigbar)")
    rows = []
    hidden = 0
    for listener in sorted(listeners, key=lambda item: (item.port, item.protocol, item.host)):
        matches = matching_services(listener, services)
        names = ", ".join(f"{item.project}/{item.name}" for item in matches) or "-"
        for pid in listener.pids or (None,):
            detail = "PID nicht sichtbar"
            relevant = bool(matches)
            if pid is not None:
                try:
                    process = inspect_process(pid)
                    relevant = relevant or any(process.cwd == root or root in process.cwd.parents
                                               for root in paths.values())
                    candidate, reason = cleanup_reason(process, listeners, services, paths, errors)
                    detail = f"{process.name}; {process.cwd}; {reason}"
                    if candidate and process.parent == 1:
                        detail += "; PPID=1 (kein Beweis für Hänger)"
                except (OSError, ValueError) as exc:
                    detail = f"Prozess nicht lesbar: {exc}"
            if not relevant and not all_ports:
                hidden += 1
                continue
            rows.append((listener.protocol, f"{listener.host}:{listener.port}",
                         str(pid or "-"), names, detail))
    print_table(("PROTOKOLL", "ADRESSE", "PID", "SPEC-ZUORDNUNG", "BEWERTUNG"), rows)
    if hidden:
        print(f"{hidden} weitere Belegungen ohne erkennbare Ecosystem-Zuordnung; anzeigen mit --all-ports")


def terminate_selected(pid: int, expected: Process, timeout: float,
                       sockets: list[Listener]) -> None:
    """Pin the process identity with a Linux pidfd before sending SIGTERM."""
    descriptor = os.pidfd_open(pid)
    try:
        current = inspect_process(pid)
        if current != expected:
            raise ValueError(f"PID {pid}: Prozessidentität hat sich geändert")
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        deadline = time.monotonic() + timeout
        selected = [item for item in sockets if pid in item.pids]
        while any(item.protocol == old.protocol and item.port == old.port
                  and address_matches(old.host, item.host)
                  for item in inspect_listeners() for old in selected):
            if time.monotonic() >= deadline:
                raise ValueError(f"PID {pid}: Port nach SIGTERM noch belegt (Mitbesitzer/Neustart möglich); "
                                 "kein automatisches SIGKILL")
            time.sleep(0.2)
        print(f"PID {pid}: SIGTERM gesendet, bisherige Listener-Adressen freigegeben")
    finally:
        os.close(descriptor)


def cleanup(pids: list[int], apply: bool, paths: dict[str, Path], timeout: float) -> int:
    code = 0
    for pid in dict.fromkeys(pids):
        try:
            services, errors = inspect_services(paths)
            listeners = inspect_listeners()
            if not any(pid in listener.pids for listener in listeners):
                raise ValueError(f"PID {pid}: kein sichtbarer Listener")
            process = inspect_process(pid)
            allowed, reason = cleanup_reason(process, listeners, services, paths, errors)
            if not allowed:
                raise ValueError(f"PID {pid}: {reason}")
            ports = [f"{item.protocol}/{item.host}:{item.port}" for item in listeners if pid in item.pids]
            print(f"{'ANWENDEN' if apply else 'VORSCHAU'} PID {pid} ({process.name}): {', '.join(ports)}")
            if apply:
                terminate_selected(pid, process, timeout, listeners)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            print(f"BEREINIGUNG FEHLER: {exc}", file=sys.stderr)
            code = 1
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Ecosystem-Root mit stackctl-Siblingmanifest")
    parser.add_argument("--cleanup-pid", type=int, action="append", default=[],
                        help="Prüfkandidat gezielt auswählen; mehrfach möglich")
    parser.add_argument("--apply", action="store_true", help="SIGTERM senden statt nur Vorschau")
    parser.add_argument("--all-ports", action="store_true", help="auch Belegungen anderer Anwendungen zeigen")
    parser.add_argument("--wait", type=float, default=5, help="Portfreigabe-Timeout in Sekunden")
    args = parser.parse_args(argv)
    if args.apply and not args.cleanup_pid:
        parser.error("--apply benötigt mindestens eine --cleanup-pid")
    if not math.isfinite(args.wait) or args.wait <= 0 or any(pid <= 1 for pid in args.cleanup_pid):
        parser.error("--wait muss positiv und jede PID größer als 1 sein")
    if args.apply and not (hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal")):
        parser.error("Bereinigung benötigt Linux und Python mit pidfd-Unterstützung")
    try:
        paths = project_paths(find_project(args.root))
        services, errors = inspect_services(paths)
        listeners = inspect_listeners()
        report(paths, services, errors, listeners, args.all_ports)
        code = cleanup(args.cleanup_pid, args.apply, paths, args.wait) if args.cleanup_pid else 0
        if args.apply:
            print("\nPORTBELEGUNG NACH BEREINIGUNG")
            services, final_errors = inspect_services(paths)
            report(paths, services, final_errors, inspect_listeners(), args.all_ports)
            code = 1 if final_errors else code
        return 1 if errors or code else 0
    except (SpecError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"service-audit: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
