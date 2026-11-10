---
project: ki-ecosystem
agent_project: ki-ecosystem
scope: architecture
purpose: Gemeinsamer Pfadbetrieb der Webanwendungen auf Uberspace 7 und 8
created: "2026-11-10 20"
updated: "2026-11-10 20"
status: draft
semantic_blocks: [hosting-goal, hosting-inventory, prefix-contract, platform-operation, implementation-order, hosting-references]
relations:
  - target: ../../README.md
    type: parent
    reason: Einstieg in das Ecosystem
  - target: ../STACKCTL.md
    type: reference
    reason: Dienstverwaltung und operative Grenzen
---

# Webhosting unter gemeinsamen Pfaden

## Ziel und Grenzen [hosting-goal]

Die Webanwendungen sollen auf Uberspace 7 und Uberspace 8 unter der jeweiligen
Standarddomain nebeneinander erreichbar sein. Gleiche Anwendungspfade auf beiden
Hosts vermeiden hostabhaengige Links; Domain, Ports und Prozessverwaltung bleiben
hostbezogene Einstellungen.

Dieses Konzept ist ein Vorschlag, kein eingerichtetes Deployment. Quellstand und
Herstellerdokumentation wurden am 2026-11-10 gesichtet; Zielhosts wurden nicht
geprueft. Pfadnamen, veroeffentlichte Anwendungen und Zugangsmodell sind noch
festzulegen.

## Anwendungen und vorgeschlagene Pfade [hosting-inventory]

| Pfad | Anwendung | Befund und Handlungsbedarf |
|---|---|---|
| `/` | Kleine Uebersichtsseite | Links auf freigegebene Anwendungen; keine Verwaltungsfunktionen |
| `/knowledge/` | `ki-knowledge` | Django/Wagtail; U7-/U8-Stages vorhanden, Deployment bisher auf Domainwurzel ausgelegt |
| `/knowledge-next/` | `ki-knowledge-next` | Eigenstaendige Django-Site; Praefixbetrieb und Produktionskonfiguration vorbereiten |
| `/assist/` | `kicli-code-assist` | Flask, gebautes Webfrontend und Socket.IO gemeinsam praefixfaehig machen |
| `/wiki/` | Optionales separates Wissenswiki | Vorzugsweise Django-Host; Solo-Server nicht unveraendert veroeffentlichen |

`yaml-cfg-wizard-ui` ist ein eingebetteter Renderer, kein eigener Webdienst.
WidgetKit und `wissenswiki-django` sind ebenfalls Bausteine der Host-Anwendungen.
Ein zusaetzliches Wiki ist nicht erforderlich, wenn die gewuenschten Funktionen
bereits in einer der Knowledge-Sites eingebunden sind.

Der Solo-Server in `wissenswiki-core/web.py` ist fuer localhost bzw. ein
vertrautes LAN ausgelegt. Seine Host-/Origin-Pruefung erwartet numerische
Serveradressen bzw. localhost und ist kein fertiges oeffentliches
HTTPS-Proxy-Deployment.

## Verbindlicher Praefixvertrag [prefix-contract]

Jede Anwendung erhaelt einen explizit konfigurierten oeffentlichen Basispfad.
Das umfasst Navigation, Redirects, Login/Logout, Formulare, Assets, Medien,
API-Aufrufe und gegebenenfalls Socket.IO. Beispielsweise gehoeren
`/assist/api/...` und `/assist/socket.io/...` zu Assist, nicht zu globalen
Routen `/api/` oder `/socket.io/`.

| Thema | Vorgabe |
|---|---|
| Proxy-Pfad | Pro Anwendung festlegen, ob das Praefix erhalten oder entfernt wird; mit Framework-Mount abstimmen |
| Django | `SCRIPT_NAME`/`FORCE_SCRIPT_NAME`, URL-Erzeugung und statische Dateien konsistent anbinden; Praefix nicht doppelt anwenden |
| Flask/Frontend | WSGI-Mount, Frontend-Buildbasis, API-Basis und Socket.IO-Pfad aufeinander abstimmen |
| Assets und Medien | Anwendungseigene URL-Pfade und getrennte Dateiverzeichnisse; keine konkurrierenden globalen `/static/`-Routen |
| Cookies | Anwendungseigene Namen und passende Cookie-Pfade; Secure-Einstellungen beibehalten |
| HTTPS | Erlaubte Hosts, CSRF-Origins und vertrauenswuerdige Proxy-Header explizit konfigurieren |
| Kanonische URLs | Verhalten fuer `/assist` und `/assist/` sowie tiefe Direktlinks festlegen |

Uberspace leitet standardmaessig den vollstaendigen Pfad weiter.
`--remove-prefix` kann das Praefix entfernen, korrigiert aber keine von der
Anwendung erzeugten Links. Ein einzelner Proxy-Schalter reicht deshalb nicht.

Unterpfade teilen dieselbe Browser-Origin und sind keine Sicherheitsgrenze.
Cookie-Pfade ersetzen keine Isolation. Verwaltungsoberflaechen brauchen
Authentifizierung und Berechtigungspruefungen; Assist mit Datei- und
Prozesszugriff darf nicht allein durch einen unbekannten Pfad geschuetzt sein.
Interne APIs, Datenbanken und Modellserver bleiben ohne oeffentliche Route.

## Betrieb auf beiden Plattformen [platform-operation]

Zunaechst die vorhandenen Uberspace-Webbackends direkt verwenden, keinen
zusaetzlichen zentralen Reverse Proxy einfuehren. Ein solcher waere erst bei
konkreten, damit nicht loesbaren Anforderungen zu begruenden.

| Aspekt | Uberspace 7 | Uberspace 8 |
|---|---|---|
| Backend-Zuordnung | `uberspace web backend set ...` | `uberspace web backend add ...` |
| Prozessverwaltung | Supervisor | systemd-User-Services |
| stackctl-Ziel | `supervisord` | `systemd-user` |
| Oeffentliche Pfade | Gemeinsames Schema | Gemeinsames Schema |

Jede eigenstaendige Anwendung behaelt ihre Python-Umgebung, Prozesse,
Konfiguration, privaten Daten und Logs. Das Ecosystem dokumentiert die
hostbezogene Zuordnung Pfad -> Dienst -> Port; die startfaehige Definition
bleibt im besitzenden Repository. Ports vor Vergabe auf Kollisionen pruefen.

Direkt durch Uberspace vermittelte Backends muessen laut beiden Handbuechern
auf `0.0.0.0` oder `::` lauschen, nicht nur auf Loopback. Das gilt nicht
pauschal fuer interne Dienste. WebSockets werden unterstuetzt; Verbindungen
brauchen Keepalives, da inaktive HTTP-Verbindungen nach drei Minuten enden.

Git push/pull synchronisiert Quellen, garantiert aber weder Neustart noch
erfolgreichen Betrieb. Plattformgerechte Dienstverwaltung und anschliessende
Erreichbarkeitspruefung gehoeren zum Deployment; keine sudo-/Systemdienste aus
historischen Polling-Beispielen ungeprueft auf Uberspace uebernehmen.

## Umsetzung und Abnahme [implementation-order]

1. Zu veroeffentlichende Sites, Pfadnamen und Zugangsschutz entscheiden.
2. Eine Django-Site als Referenz fuer den Praefixbetrieb waehlen; vorhandene
   Deployment-Pruefungen einschliesslich Wagtail-Basis-URL und Asset-Pfaden
   anpassen, statt nur Proxy-Regeln hinzuzufuegen.
3. Unter einem Nicht-Root-Pfad Navigation, tiefe Direktlinks, Anmeldung,
   Redirects, Formulare, Assets und API pruefen; Root-Betrieb erhalten.
4. Weitere Sites nach demselben Vertrag anbinden; bei Assist auch
   Socket.IO-Verbindungsaufbau und Wiederverbindung pruefen.
5. Je Zielhost Backend-Regeln, Prozessverwaltung, Portbelegung, Neustart und
   parallelen Zugriff abnehmen. Ressourcenbedarf messen, nicht aus der Anzahl
   ausgecheckter Repositories ableiten.

## Quellen [hosting-references]

- [Uberspace 7: Webbackends](https://manual.uberspace.de/web-backends/)
- [Uberspace 8: Webbackends](https://u8manual.uberspace.de/web_backends/)
- [Uberspace 8: Unterschiede zu U7](https://u8manual.uberspace.de/first_u7/)
- [stackctl im Ecosystem](../STACKCTL.md)
- [Knowledge-U7-Stage](../../../ki-knowledge/config/stages/prod-uberspace7.yaml)
- [Knowledge-U8-Stage](../../../ki-knowledge/config/stages/prod-uberspace8.yaml)
