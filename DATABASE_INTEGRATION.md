# 📊 Database Integration Guide - Supabase + Scraper

**Jak zintegrować Supabase z Pralkowcy Scraper**

---

## 🎯 Architektura Pipeline'u

```
┌─────────────┐
│   Scraper   │ (pobiera z elektorda.pl)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Analyzer   │ (Claude analizuje dane)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  Google Drive/Sheets Sync   │ (backup w chmurze)
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Supabase Database Sync     │ (główna baza danych)
└─────────────────────────────┘
```

---

## 📋 Co Robią Tabele

### `kody_bledow` — Główna baza kodów
```sql
kod VARCHAR(10)          — Kod błędu (E19, F04, itd.)
model VARCHAR(255)       — Model urządzenia (Bosch zmywarka)
usterka TEXT             — Opis problemu
symptomy TEXT[]          — Objawy (array)
rozwiazanie JSONB        — Kroki naprawy (JSON)
czesc_zamenna VARCHAR    — Numer części
koszt_czesci INTEGER     — Cena w PLN
czas_naprawy_min INT     — Czas naprawy w minutach
quality_score FLOAT      — Ocena jakości (0-1)
```

### `pytania_zadane` — Deduplikacja
```sql
kod VARCHAR(10)          — Kod już pytany
data_zadania DATE        — Kiedy pytaliśmy
found BOOLEAN            — Czy znaleziono
zrodlo VARCHAR(50)       — Źródło (elektorda.pl)
```

### `logi_scrapingu` — Metryki sesji
```sql
data DATE                — Data sesji
phase VARCHAR(20)        — phase1 lub phase2
requests_total INT       — Ile requestów
requests_found INT       — Ile znaleziono
status VARCHAR(20)       — success/partial/error
manifest_json JSONB      — Pełny manifest
```

---

## 🚀 KROK PO KROKU

### **Krok 1: Setup Supabase** (15 minut)

Przeczytaj: `SUPABASE_SETUP.md`

✓ Projekt Supabase stworzony  
✓ Tabele utworzone (SQL query)  
✓ API Keys skopiowane  
✓ Environment variables ustawione  

### **Krok 2: Zainstaluj Biblioteki** (2 minuty)

```bash
pip install -r requirements.txt --break-system-packages
```

Sprawdź czy `supabase` jest zainstalowany:
```bash
python -c "import supabase; print('OK')"
```

### **Krok 3: Test Modułu** (5 minut)

```bash
python scripts/database.py
```

Powinna być:
```
✓ Supabase client initialized
✓ Database module: OK
```

### **Krok 4: Test Pipeline'u** (10 minut)

```bash
python main.py
```

Powinna być:
```
🚀 PRALKOWCY SCRAPER - FULL PIPELINE START

📡 PHASE 1: SCRAPING FROM ELEKTORDA
✓ Scraper completed

🔍 PHASE 2: ANALYZING DATA
✓ Analyzed 0 codes (mock data)

📊 PHASE 3: UPLOADING TO GOOGLE DRIVE/SHEETS
ℹ️  Google Drive sync disabled

💾 PHASE 4: DATABASE SYNC (SUPABASE)
✓ Database sync: offline (check env variables)

✅ PIPELINE COMPLETE
```

---

## 🔧 Konfiguracja

### Environment Variables

Ustawisz je w `SUPABASE_SETUP.md`, ale na wypadek tutaj:

```bash
# Windows PowerShell
$env:SUPABASE_URL = "https://xxxxxxxxxxxxx.supabase.co"
$env:SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Sprawdzenie
echo $env:SUPABASE_URL
```

### settings.json

Nie wymagane, ale opcjonalnie możesz dodać:

```json
{
  "google_drive": {
    "parent_folder_id": "YOUR_ID",
    "spreadsheet_id": "YOUR_ID",
    "enabled": true
  },
  "database": {
    "type": "supabase",
    "table_codes": "kody_bledow",
    "table_asked": "pytania_zadane",
    "table_logs": "logi_scrapingu"
  }
}
```

---

## 💾 Jak Dane Trafiają do Bazy

### 1. Scraper pobiera dane z elektorda.pl
```python
# scripts/scraper.py
url = "https://elektorda.pl/szukaj?q=E19"
# ... pobiera HTML
```

### 2. Analyzer parsuje dane
```python
# scripts/analyzer.py
parsed_data = [
    {
        "kod_bledu": "E19",
        "model": "Bosch zmywarka",
        "usterka": {"przyczyna": "Elektrozawór", "symptomy": [...]},
        "rozwiazanie": {"kroki": [...], "czas_minut": 30},
        ...
    }
]
```

### 3. Main.py koordynuje
```python
# main.py
parsed_data, manifest = run_analyzer()

# Google sync
gdrive_result = sync_to_google(parsed_data, manifest, ...)

# Database sync
db_result = sync_to_database(parsed_data, manifest, ...)
```

### 4. database.py wysyła do Supabase
```python
# scripts/database.py
supabase.table("kody_bledow").upsert({
    "kod": "E19",
    "model": "Bosch zmywarka",
    "usterka": "Elektrozawór",
    ...
})
```

### 5. Baza przechowuje na wieki
```sql
SELECT * FROM kody_bledow WHERE kod = 'E19';
-- ✓ E19 | Bosch zmywarka | Elektrozawór | ...
```

---

## 🧪 Sprawdzanie Danych

### Wejdź do Supabase Dashboard

1. https://app.supabase.com
2. Projekt: `pralkowcy-scraper`
3. Zakładka: **Table Editor**

### Opcja A: Kody błędów
```sql
SELECT kod, model, quality_score, updated_at
FROM kody_bledow
ORDER BY updated_at DESC
LIMIT 10;
```

### Opcja B: Historia scrapingu
```sql
SELECT data, phase, requests_total, status
FROM logi_scrapingu
ORDER BY data DESC
LIMIT 10;
```

### Opcja C: Które kody już pytaliśmy
```sql
SELECT kod, data_zadania, found
FROM pytania_zadane
WHERE found = true
ORDER BY data_zadania DESC;
```

---

## 📈 Fallback — Co Jeśli Supabase Nie Działa?

Jeśli `SUPABASE_URL` lub `SUPABASE_KEY` nie są ustawione:

```
⚠️  Supabase not available (check env variables)
ℹ️  Skipping database sync (will try on next run)
```

**Pipeline dalej działa!** Dane trafiają do:
- ✅ Google Drive (backup)
- ✅ Google Sheets (raporty)
- ✅ Logi lokalne

Kiedy Internet/Supabase będą dostępne, dane się zsynchronizują.

---

## 🔐 Bezpieczeństwo

### API Key — jaką wybrać?

**`anon public`** (Public Key)
- ✅ Dla scraper'a
- ✅ Publiczny dostęp
- ✅ Ograniczone RLS

**`service_role`** (Secret Key)
- ❌ NIGDY do scriptu!
- ✅ Tylko na serwerze backend'u
- ⚠️ Pełny dostęp do bazy

### Ochrona Klucza

```bash
# .gitignore
.env
.env.local
config/*key*
logs/*.log
```

---

## 🆘 Troubleshooting

### Problem: `SUPABASE_URL not set`

```bash
# Sprawdzenie
python -c "import os; print(os.getenv('SUPABASE_URL'))"

# Jeśli None, ustaw:
$env:SUPABASE_URL = "https://..."
```

### Problem: `Table kody_bledow does not exist`

```bash
# Sprawdzenie czy SQL się uruchomił
# Wejdź do Supabase → SQL Editor
# Sprawdzaj czy CREATE TABLE wykonał się bez błędów
```

### Problem: `Permission denied`

```bash
# Sprawdzenie uprawnień w Supabase
# Settings → Database → Row Level Security
# Możliwe że RLS blokuje dostęp
```

### Problem: `400 Bad Request`

```bash
# Sprawdzenie formatu danych
tail -50 logs/database_*.log

# Możliwe że dane nie zgadzają się z typem kolumny
# np. integer zamiast text
```

---

## 📊 Statystyki i Raporty

### SQL View'y (już w bazie)

```sql
-- Ostatnie kody
SELECT * FROM latest_codes LIMIT 10;

-- Statystyki scrapingu
SELECT * FROM scrape_stats;

-- Kody bez rozwiązania
SELECT * FROM codes_without_solution;
```

### Python Query

```python
from scripts.database import get_supabase_client

supabase = get_supabase_client()

# Ostatnie kody
result = supabase.table("kody_bledow").select("*").order("updated_at", desc=True).limit(10).execute()
print(result.data)

# Statystyki
result = supabase.rpc("get_stats", {}).execute()
```

---

## 🚀 Automatyzacja (GitHub Actions)

Jeśli chcesz automatyczne uruchamianie co dzień:

```yaml
# .github/workflows/scraper_with_db.yml
name: Pralkowcy Scraper + Database

on:
  schedule:
    - cron: '0 2 * * *'  # Każdego dnia o 2:00 AM

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r elektorda_scraper/requirements.txt
      
      - name: Run pipeline with database
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          GOOGLE_DRIVE_FOLDER: ${{ secrets.GOOGLE_DRIVE_FOLDER }}
          GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
        run: |
          cd elektorda_scraper
          python main.py
      
      - name: Commit results
        run: |
          git config user.email "bot@pralkowcy.pl"
          git config user.name "Pralkowcy Bot"
          git add logs/ data/ reports/
          git commit -m "✓ Scrape + Sync $(date +%Y-%m-%d)" || true
          git push
```

---

## ✅ Checklist Integracji

- [ ] Supabase projekt stworzony
- [ ] Tabele utworzone (SQL query uruchomiony)
- [ ] API Keys skopiowane
- [ ] `SUPABASE_URL` i `SUPABASE_KEY` ustawione
- [ ] `database.py` testuje się (✓ OK)
- [ ] `main.py` testuje się (✓ OK)
- [ ] Dane trafiają do Supabase (sprawdzono w Table Editor)
- [ ] Logi są w `logs/database_*.log`
- [ ] `.gitignore` zawiera `.env` i klucze
- [ ] Pipeline automatyzuje się (GitHub Actions, cron, itd.)

---

## 📚 Dokumentacja

- **SUPABASE_SETUP.md** — Setup Supabase
- **GDRIVE_SETUP.md** — Setup Google Drive
- **INTEGRATION_GUIDE.md** — Integracja z main.py
- **scripts/database.py** — Dokumentacja kodu

---

## 🎉 Gotowe!

Teraz masz:
- ✅ PostgreSQL bazę na Supabase
- ✅ Python moduł `database.py`
- ✅ Kompletny pipeline z bazą danych
- ✅ Fallback na Google Drive
- ✅ Logi wszystkiego

**Powodzenia!** 🚀
