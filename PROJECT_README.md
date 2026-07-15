# 🔧 Pralkowcy Scraper — Projekt Kompletny

**Automatic Web Scraper + AI Analysis + Cloud Storage**

---

## 📖 Spis Treści

1. [Overview](#overview)
2. [Architektura](#architektura)
3. [Szybki Start](#szybki-start)
4. [Dokumentacja](#dokumentacja)
5. [Struktura Projektu](#struktura-projektu)
6. [Problemy?](#problemy)

---

## 🎯 Overview

**Pralkowcy Scraper** to kompletne rozwiązanie do:

- 🌐 **Scrapowania** kodów błędów z elektorda.pl
- 🤖 **Analizy AI** (Claude) — wyciąga rozwiązania
- ☁️ **Backupu** do Google Drive + Sheets
- 💾 **Bazy Danych** PostgreSQL (Supabase)
- 📊 **Raportowania** + Logowania
- ⚙️ **Automatyzacji** (GitHub Actions, cron)

**Status:** ✅ Produkcja-ready

---

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────┐
│  PRALKOWCY SCRAPER - Full Pipeline                  │
└─────────────────────────────────────────────────────┘

1. SCRAPER (scripts/scraper.py)
   └─ Pobiera HTML z elektorda.pl
   └─ Extrahuje kody błędów (E19, F04, itd.)
   └─ Zapisuje RAW w data/raw/

2. ANALYZER (scripts/analyzer.py)
   └─ Claude AI analizuje wątki
   └─ Wyciąga: usterka, rozwiązanie, części
   └─ Ocenia jakość (0-1)
   └─ Tworzy JSON structured

3. GDRIVE_UPLOADER (scripts/gdrive_uploader.py)
   └─ Uploaduje na Google Drive
   └─ Dodaje wiersze do Google Sheets
   └─ Tworzy foldery dzienne
   └─ Backup w chmurze ☁️

4. DATABASE (scripts/database.py)
   └─ Synchronizuje do Supabase PostgreSQL
   └─ UPSERT do kody_bledow
   └─ INSERT logs do logi_scrapingu
   └─ Deduplikacja w pytania_zadane
   └─ Fallback jeśli offline

5. LOGGER (everywhere)
   └─ Wszystko logowane
   └─ Pliki w logs/
   └─ Queryable SQL views
```

---

## ⚡ Szybki Start

### 1. Klonuj / Przygotuj

```bash
cd C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper
```

### 2. Setup Supabase (5 minut)

```bash
# Przeczytaj
cat QUICK_START_DATABASE.md

# Lub pełna dokumentacja
cat SUPABASE_SETUP.md
```

### 3. Setup Google Drive (10 minut)

```bash
# Przeczytaj
cat QUICK_START_GDRIVE.md

# Lub pełna dokumentacja
cat GDRIVE_SETUP.md
```

### 4. Zainstaluj Biblioteki

```bash
pip install -r requirements.txt --break-system-packages
```

### 5. Test

```bash
# Test database
python scripts/database.py

# Test całej pipeline'y
python main.py
```

**Output powinien być:**
```
✅ PIPELINE COMPLETE
```

---

## 📚 Dokumentacja

### Dla Setup'u

| Plik | Zawartość |
|------|-----------|
| **QUICK_START_DATABASE.md** | 5-minutowy setup Supabase |
| **SUPABASE_SETUP.md** | Pełny setup PostgreSQL |
| **QUICK_START_GDRIVE.md** | 5-minutowy setup Drive |
| **GDRIVE_SETUP.md** | Pełny setup Google Drive |
| **.env.example** | Template zmiennych |

### Dla Integracji

| Plik | Zawartość |
|------|-----------|
| **main.py** | Pełny orchestrator |
| **DATABASE_INTEGRATION.md** | Jak działa baza + query's |
| **INTEGRATION_GUIDE.md** | Jak integrować z kodem |

### Dla Raportowania

| Plik | Zawartość |
|------|-----------|
| **WORK_SUMMARY_DATABASE_2026-07-12.md** | Co napisano (baza) |
| **WORK_SUMMARY_2026-07-12.md** | Co napisano (Drive) |
| **PROJECT_README.md** | Ten plik |

---

## 📁 Struktura Projektu

```
elektorda_scraper/
│
├── scripts/                    # Python modules
│   ├── scraper.py             # Pobiera z elektorda.pl
│   ├── analyzer.py            # Claude analizuje
│   ├── gdrive_uploader.py     # Upload do Drive/Sheets
│   └── database.py            # Sync do Supabase
│
├── db/                         # Database
│   └── 001_create_tables.sql  # SQL migrations
│
├── config/                     # Konfiguracja
│   ├── settings.json          # Ustawienia scrapera
│   └── pralkowcy-scraper-*.json  # Google credentials (NIE COMMIT!)
│
├── data/                       # Dane (generated)
│   ├── raw/                   # Surowy HTML
│   ├── parsed/                # JSON strukturyzowany
│   └── manifests/             # Metadane sesji
│
├── reports/                    # Raporty
│   ├── daily/                 # Codzienne raporty
│   └── archive/               # Archiwum
│
├── logs/                       # Logi (generated)
│   ├── scraper_*.log
│   ├── database_*.log
│   └── main_*.log
│
├── main.py                     # Orchestrator (START TUTAJ!)
├── requirements.txt            # Python dependencies
├── .env.example                # Env template
├── .gitignore                  # Git ignore (klucze!)
│
└── docs/                       # Dokumentacja
    ├── QUICK_START_DATABASE.md
    ├── SUPABASE_SETUP.md
    ├── DATABASE_INTEGRATION.md
    ├── GDRIVE_SETUP.md
    ├── INTEGRATION_GUIDE.md
    └── PROJECT_README.md (ten plik)
```

---

## 🚀 Uruchomienie

### Localnie (raz)

```bash
cd elektorda_scraper
python main.py
```

### Codziennie (Scheduler)

**Windows Task Scheduler:**
```
New Task → Run: python main.py
Schedule: Daily at 2:00 AM
```

**GitHub Actions:**
```yaml
# .github/workflows/scraper.yml
on:
  schedule:
    - cron: '0 2 * * *'
```

### Live Monitoring

```bash
# Watch logs
tail -f logs/main_*.log

# Database
https://app.supabase.com (Table Editor)

# Drive
https://drive.google.com (look for Raport_*)

# Sheets
https://docs.google.com/spreadsheets (see rows)
```

---

## 🗄️ Baza Danych

### Tabele

| Tabela | Cel | Wiersze |
|--------|-----|---------|
| `kody_bledow` | Wszystkie kody błędów | 1000+ |
| `pytania_zadane` | Deduplikacja | 10000+ |
| `logi_scrapingu` | Metryki sesji | 365+ (roczne) |

### SQL Views (dla raportów)

```sql
-- Ostatnie znalezione kody
SELECT * FROM latest_codes LIMIT 50;

-- Statystyki scrapingu
SELECT * FROM scrape_stats;

-- Kody bez rozwiązania
SELECT * FROM codes_without_solution;
```

### Python Query

```python
from scripts.database import get_supabase_client

supabase = get_supabase_client()
codes = supabase.table("kody_bledow").select("*").execute()
print(codes.data)
```

---

## 📊 Monitorowanie

### Logi

```bash
# Dzisiejsze logi
ls logs/ | grep "2026-07-12"

# Ostatnie błędy
grep ERROR logs/main_*.log | tail -20

# Status bazy
grep "database" logs/main_*.log
```

### Statystyki

```bash
# Ile kodów znalezionych dzisiaj?
tail -100 logs/scraper_*.log | grep "SUCCESS"

# Ile zainserted do bazy?
tail -100 logs/database_*.log | grep "Inserted"

# Google Drive sync?
tail -100 logs/gdrive_*.log | grep "✓"
```

---

## 🔒 Bezpieczeństwo

### Chronić Klucze!

```bash
# .gitignore
.env
.env.local
config/*key*
config/*credentials*
logs/
```

### Environment Variables

```bash
# PowerShell
$env:SUPABASE_URL = "https://..."
$env:SUPABASE_KEY = "eyJ..."

# Sprawdzenie
echo $env:SUPABASE_URL
```

### Google Credentials

- Trzymaj w `config/` (NOT public)
- Nie commituj do Git'a
- Rotate co 6 miesięcy

---

## ⚠️ Problemy?

### Database: `SUPABASE_URL not set`

```bash
# Sprawdzenie
python -c "import os; print(os.getenv('SUPABASE_URL'))"

# Jeśli None, ustaw:
$env:SUPABASE_URL = "..."
```

### Drive: `403 Forbidden`

Folder nie jest udostępniony Service Account:
```
Supabase → Settings → Database
Sprawdź czy RLS nie blokuje dostępu
```

### Scraper: `Connection timeout`

```
elektorda.pl może być down
Zwiększ delay w settings.json:
"delay_max_sec": 15
```

### Logs: `Permission denied`

```bash
# Sprawdzenie uprawnień
ls -la logs/
chmod 755 logs/
```

**Więcej help?** Czytaj logi! 📋

```bash
tail -50 logs/main_*.log
```

---

## 📞 Support

- 📖 Dokumentacja: przeczytaj 4-5 plików .md
- 📝 Logi: `logs/*.log`
- 💬 Błędy: Google'uj + Stack Overflow
- 🐛 Bugs: GitHub Issues (jeśli jest repo)

---

## 🎓 Nauka

### Jak to działa?

1. **Scraper** — BeautifulSoup + requests
2. **Analyzer** — Claude API + regex
3. **GDrive** — Google API (sheets + drive)
4. **Database** — Supabase SDK + PostgreSQL SQL
5. **Orchestrator** — Python main.py

### Przydatne links

- [BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup/)
- [Claude API](https://console.anthropic.com)
- [Google Drive API](https://developers.google.com/drive/api)
- [Supabase Docs](https://supabase.com/docs)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

## 📝 Changelog

### v1.0 (2026-07-12)
- ✅ Scraper + Analyzer
- ✅ Google Drive Integration
- ✅ Supabase PostgreSQL
- ✅ Main Orchestrator
- ✅ Full Documentation

### v1.1 (Planned)
- ⏳ Slack Notifications
- ⏳ Dashboard (HTML)
- ⏳ CLI Tools
- ⏳ Advanced Filtering

---

## 📄 License

MIT (jeśli public repo)

---

## 👨‍💻 Author

**Claude (Haiku 4.5)** — 2026-07-12

---

## 🎉 Gotowe!

Masz kompletne rozwiązanie do automatyzacji scrapowania + analizy + storage.

**Powodzenia!** 🚀

---

### ⚡ Quick Links

```
Szybki Start → QUICK_START_DATABASE.md
Setup Drive  → QUICK_START_GDRIVE.md
Uruchomienie → python main.py
Logi        → logs/
Baza Danych → https://app.supabase.com
Dokumenty   → https://drive.google.com
```

**Start tutaj:** `python main.py` 🚀
