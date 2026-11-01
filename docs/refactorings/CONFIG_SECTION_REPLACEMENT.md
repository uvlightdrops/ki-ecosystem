---
project: ki-ecosystem
agent_project: ki-ecosystem
scope: [yaml-cfg-wizard, ki-core]
purpose: Resolver-Kopie bereinigen
created: 2026-11-01
updated: 2026-11-01
---

# Strategie: Konfigurationsabschnitte explizit ersetzen

| Frage | Entscheidung / Stand |
|-------|----------------------|
| Anlass | Resolver-Kopie verlor Replacement-Grenzen und ignorierte `stages_dir`; App-Stages nutzen den Marker bereits. |
| Strategie | 1. Gemeinsame Merge-Logik; 2. ki-core-Kopie entfernen; 3. Regressionen absichern. Lokal umgesetzt. |
| Zustaendigkeit | `yaml-cfg-wizard`: generische Semantik; `ki-core`: Aktivierung und abschliessender Merge. |
| Vertrag | `__replace__: true` entfernt geerbte Dictionary-Schluessel; hoehere Schichten duerfen Werte hinzufuegen. `false`: normales Merge; andere Werte: Fehler. |
| Kompatibilitaet | Bibliothek nur per Opt-in; Listen weiterhin vollstaendig ersetzen. |
| Kritische Grenze | Marker bis nach Credentials und Schema-Defaults behalten; erst dann entfernen. Keine Wiederbelebung entfernter Eintraege. |
| Interne API | `resolve(preserve_replace_markers=True)` validiert markerfrei, behaelt aber Merge-Metadaten. Nicht als App-Ergebnis ausgeben. |
| Nachweise | 32 Bibliothekstests, 33 gezielte ki-core-Tests; beide Wheels gebaut. Lokale Editable-Checkouts. |
| Code-Commits | `yaml-cfg-wizard`: `7962072`; `ki-core`: `70ccb3c`. |
| Bereitstellung | Zuerst `yaml-cfg-wizard>=0.3.0`, dann angepasstes `ki-core`. Noch kein Push, Release oder Deployment. |
| Nicht umfasst | Separate App-/Go-Loader, Stage-Dateien, Dienste; bestehende Gesamtvalidierungsgrenzen bleiben. |

API-Details: `yaml_cfg_wizard/README.md`; Integration: `ki-core/README.md`.
