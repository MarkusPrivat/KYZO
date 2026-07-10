# KYZO: Next-Gen Education

Lernen, das sich dir anpasst. Schlauer lernen mit deinem AI-Buddy.

KYZO ist eine KI-gestützte adaptive Lernplattform, die analoge Hausaufgaben (Fotos/PDFs) in strukturierte Lerneinheiten umwandelt und personalisierte Übungstests generiert. Das Ziel: Schüler lernen nicht nur aus der Lösung, sondern gezielt aus den Schwachstellen ihrer eigenen Aufgaben.

## Inhaltsverzeichnis

- [Was ist KYZO?](#was-ist-kyzo)
- [Quickstart](#quickstart)
- [Architektur](#architektur)
- [AI-Pipeline](#ai-pipeline)
  - [Modellvergleiche](#modellvergleiche)
    - [Textextraktion (OCR)](#textextraktion-ocr)
    - [Fragengenerierung](#fragengenerierung)
- [Projektstruktur](#projektstruktur)
- [Konfiguration](#konfiguration)
- [Datenbank & Seeding](#datenbank--seeding)
- [Tests](#tests)
- [API-Dokumentation](#api-dokumentation)
- [Roadmap](#roadmap)
- [Beitragen](#beitragen)
- [Lizenz](#lizenz)

## Was ist KYZO?

KYZO schließt die Lücke zwischen Aufgabe und gezieltem Üben. Bestehende KI-Tools geben oft nur die Lösung aus — ohne den Lernprozess nachhaltig zu fördern. KYZO geht einen Schritt weiter:

1. **Hausaufgaben analysieren** — Fotos oder PDFs von Arbeitsblättern werden per OCR extrahiert und in strukturierte Daten umgewandelt
2. **Kompetenz-Profil führen** — Jeder Schüler erhält ein persönliches Profil, das den Wissensstand über die Zeit abbildet
3. **Maßgeschneiderte Tests generieren** — Basierend auf historischen Schwachstellen werden adaptive Übungstests erstellt
4. **Feedback & Tipps geben** — Nach Testabschluss erfolgt eine Auswertung mit gezielten Vertiefungsempfehlungen

## Quickstart

### Voraussetzungen

- Python >= 3.12
- `OPENAI_API_KEY` und/oder `GEMINI_API_KEY` (als API-Token)

### Installation

```bash
git clone git@github.com:MarkusPrivat/KYZO.git
cd KYZO
pip install -e .          # editable install
pip install -e ".[dev]"   # + dev dependencies
```

### Konfiguration

Kopiere die Umgebungsvariablen-Vorlage und trage deine API-Schlüssel ein:

```bash
cp apps/kyzo_backend/.env_template apps/kyzo_backend/.env
# Bearbeite apps/kyzo_backend/.env mit deinen Schlüsseln
```

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API-Schlüssel | `sk-...` |
| `GEMINI_API_KEY` | Google Gemini API-Schlüssel | `AIza...` |
| `AUTH_SECRET_KEY` | JWT Signing Key (min. 32 Bytes) | `openssl rand -hex 32` |

### Starten der Anwendungen

**Backend:**

```bash
python apps/kyzo_backend/run_backend.py
# Läuft auf http://127.0.0.1:8000
```

**Frontend:**

```bash
python apps/kyzo_frontend/run.py
# Läuft auf dem Flask Dev-Port (standardmäßig 5000)
```

## Architektur

### Tech Stack

| Bereich | Technologie |
|---|---|
| **Sprache & Framework** | Python 3.12+, FastAPI, Uvicorn, Pydantic v2 |
| **Datenbank** | SQLite, SQLAlchemy 2.0 ORM |
| **KI / LLM (Primär)** | Gemini 3.1 Flash Lite |
| **KI / LLM (Fallback)** | GPT-4o-mini |
| **Authentifizierung** | JWT (PyJWT, HS256), pwdlib (Argon2/Bcrypt) |
| **Infrastruktur & Dev** | dotenv, pydantic_settings, slowapi, pdf2image, Pillow, pylint, pytest |

### Schichtenmodell

```
┌───────────────────── API Layer ─────────────────────┐
│  UserRouter │ KnowledgeRouter │ QuestionRouter │ TestRouter  │
├────────────────── Manager Layer (Business Logic) ────┤
│  UserManager │ KnowledgeManager │ QuestionManager │ TestManager │
├──────────── Service Layer (External / Cross-Cutting) ┤
│  AuthService │ LLMOrchestrator │ ImageProcessing     │
│  GoogleGenAIService │ OpenAIService                   │
├────────── Data Layer (SQLAlchemy Models) ────────────┤
│  User │ Subject │ Topic │ Question │ Test │ ...       │
└──────────── Storage Layer (SQLite) ──────────────────┘
```

**Manager Layer im Detail:**

- **UserManager** — Account-Lebenszyklus, CRUD mit Transaktionssicherheit, Soft Delete, Partial Updates
- **KnowledgeManager** — Validierung und Persistenz von Fächern (Subjects) und Themen (Topics), Wissensbaum-Integrität
- **QuestionManager** — Lebenszyklus von Aufgaben, asynchrone Multi-Provider KI-Generierung (Gemini primär, GPT-Fallback), OCR-Konvertierung in JSON-Draft bis zur Freigabe
- **TestManager** — Adaptive Übungstests, gewichtete zufällige Frageauswahl, Echtzeit-Metriken (Bearbeitungszeit, Antwortvalidierung)

## AI-Pipeline

Die Pipeline transformiert unstrukturierte Quellmedien vollautomatisch in didaktisch hochwertige Lerneinheiten:

```
Medien-Input → Vision & Textextraktion → Didaktische Generierung → Schema-Validierung & DB
   (Foto/PDF)      (OCR + Confidence)       (MC-Fragen erstellen)     (Pydantic V2)
```

| Schritt | Beschreibung |
|---|---|
| **01 — Medien-Input** | Smartphone-Foto oder PDF-Scan eines Arbeitsblatts; asynchroner Upload & Bild-Vorbereitung (`pdf2image` / `Pillow`) |
| **02 — Vision & Textextraktion** | Gemini 3.1 Flash Lite extrahiert den Text mit Confidence-Score und gibt strukturierten JSON-Rohtext zurück |
| **03 — Didaktische Generierung** | Erstellung von Multiple-Choice-Fragen inkl. Distraktoren (falsche Antworten) und Erklärungen; strukturierter JSON-Draft |
| **04 — Schema-Validierung & DB** | Pydantic V2 erzwingt strikte JSON-Struktur, Persistenz in der Datenbank mit Status `draft` bis zur manuellen Freigabe |

### Modellvergleiche

Alle evaluierten Modelle wurden unter identischen Systembedingungen mit einer Temperatur von 0.3 getestet — für ein optimales Verhältnis zwischen deterministischer Strukturtreue und sprachlicher Flexibilität. Die Benchmarks dienten der fundierten Entscheidung für die primäre KI-Engine (Gemini) und das Fallback-Modell (GPT).

#### Textextraktion (OCR)

**Testaufbau:** Bildschirmfoto eines gedruckten Übungsblatts mit Lückentext und separat vorgegebenen Textbausteinen. Herausforderung: unvollständigen Lückentext erfassen und die Bausteine logisch integrieren.

| Modell | Kosten / Request | Token | Urteil |
|---|---|---|---|
| **Gemma 4 26b** (Autark) | Kostenlos | 1.170 | Solide Schema-Treue und Token-Effizienz, aber didaktischer Transfer unvollständig — bindet Lückentexte und Nummerierungen nicht vollständig ein |
| **Gemini 3.1 Flash Lite** (Empfehlung) | ~0,001 € | 2.038 | Absolut fehlerfreie Texterfassung; korrigiert proaktiv Schreibfehler des Scans; ergänzt Lückentexte didaktisch sinnvoll; Kosten ca. 1/6 von OpenAI |
| **GPT-4o Mini** (Fallback) | ~0,0059 € | 37.863 | Korrekt strukturierte JSON-Ausgabe, aber halluzinierte 4 zusätzliche Rechtschreibfehler; ignorierte Anforderung zur Lückentext-Vervollständigung; extrem hoher Token-Verbrauch bei Bilddaten |

#### Fragengenerierung

**Testaufbau:** Unstrukturierter Fließtext über das *Antike Griechenland* (Text-zu-Text, keine OCR). Vorgabe: genau 5 Multiple-Choice-Fragen für Schüler der 6. Klasse mit selbstständig definiertem und abgestuftem Schwierigkeitsgrad bei fehlerfreier JSON-Syntax.

| Modell | Kosten / Request | Token | Urteil |
|---|---|---|---|
| **Gemma 4-26b-it** (Autark) | Kostenlos | 3.175 | Generierte in 60 % der Fälle fehlerhaft mehrere korrekte Antworten; orthografische Fehler und Syntax-Artefakte; riskante JSON-Stabilität — für automatisierte Tests unbrauchbar |
| **Gemini 3.1 Flash Lite** (Empfehlung) | ~0,002 € | 3.324 | Plausible Distraktoren und logische "Warum"-Erklärungen; präzise Fragen auf dem Niveau moderner Lehrwerke; exzellente JSON-Stabilität — uneingeschränkte Empfehlung trotz leicht höherer Kosten |
| **GPT-4o-mini** (Fallback) | ~0,001 € | 3.886 | Kosteneffizient im reinen Text-In/Out; fehlerfreie Syntax-Konformität, aber mangelnde Faktentreue in Einzelfällen (Falschinformationen) — gut für Dev-Tests, unmoderiert im Live-Betrieb ein Ausschlusskriterium |

**Fazit:** Gemini 3.1 Flash Lite wurde als primäres Modell gewählt und GPT-4o-mini als Fallback bei Ausfällen der Gemini-API.

## Projektstruktur

```
KYZO/
├── apps/
│   ├── kyzo_backend/          # FastAPI Backend
│   │   ├── api/               # Route-Handler (question, test, user, knowledge)
│   │   ├── config/            # Konfiguration & Prompts
│   │   ├── core/              # Datenbank-Setup
│   │   ├── data/              # SQLAlchemy Models
│   │   ├── managers/          # Business Logic Layer
│   │   ├── schemas/           # Pydantic Schemas (Request/Response)
│   │   ├── scripts/           # Seeding & Migrationsskripte
│   │   └── services/          # AI-Integration, Auth, Image Processing
│   │       ├── auth_service.py
│   │       ├── google_gen_ai_service.py
│   │       ├── llm_orchestrator.py
│   │       └── openai_service.py
│   └── kyzo_frontend/         # Flask Frontend (Jinja-Templates)
│       ├── routes/            # Seitenrouten
│       └── templates/         # HTML-Vorlagen
├── tests/                     # pytest Tests
├── pyproject.toml             # Dependencies & Tool-Konfiguration
└── LICENSE
```

## Datenbank & Seeding

Die Anwendung verwendet SQLite (`apps/kyzo_backend/data/kyzo-data.sqlite`). Schema und Tabellen werden automatisch beim ersten Start erstellt.

### Sample-Daten einspielen

```bash
python apps/kyzo_backend/scripts/run_seeding.py
```

Dies legt eine lokale SQLite-Datenbank an und befüllt sie mit Beispiel-Benutzern, Fächern, Themen und Frage-Eingaben.

## Tests

```bash
pytest tests/ -v
```

Die Tests befinden sich im `tests/`-Verzeichnis, strukturiert nach App (`kyzo_backend`, `kyzo_frontend`).

## API-Dokumentation

Nach dem Start des Backends ist die Swagger UI unter folgender URL erreichbar:

> http://127.0.0.1:8000/docs

Dort kannst du alle Endpunkte interaktiv testen — inklusive Fragen erstellen, Tests verwalten und Benutzeroperationen durchführen. Das Backend stellt **37 API-Endpunkte** in 4 Router-Modulen bereit.

## Roadmap

### Kurzfristig (MVP Polish)
- Frontend-Feinschliff: UI/UX-Komponenten finalisieren
- Backend-Asynchronität: performante, parallele Request-Verarbeitung
- Code-Refactoring: systematische Reviews und architektonische Bereinigung

### Mittelfristig (Adaptive Intelligence)
- Kompetenz-Scoring: Algorithmus zur präzisen Abbildung von Schülerfähigkeiten
- Dynamische Selektion: KI-gestützte Auswahl maßgeschneiderter Fragestellungen je nach Lernstand
- Format-Diversifizierung: Erweiterung um offene und hybride Aufgabenformate

### Langfristig (Real-World Ingestion)
- Private Erprobung im familiären Umfeld
- Klasseninterner Einsatz in Kooperation mit Lehrkräften
- Validierung des autarken Setups unter echten Schulbedingungen

## Beitragen

Beiträge sind willkommen. Bitte halte dich an folgende Schritte:

1. **Fork** das Repository
2. Erstelle einen Feature-Branch (`feature/mein-feature`)
3. Commere deine Änderungen mit klaren Commit-Messages
4. Push auf den Branch und öffne einen Pull Request gegen `main`

## Lizenz

[MIT License](LICENSE) - Copyright (c) 2026 Markus
