# Elektorda Scraper - Setup & Usage

Profesjonalny scraper do zbierania kodów błędów z forum elektorda.pl dla Pralkowcy.

## 📋 Wymagania

- Python 3.9+ (najlepiej 3.11+)
- Windows/Mac/Linux
- Dostęp do internetu
- Konto Supabase (opcjonalnie, ale rekomendowane)
- Gmail account z App Password (do maila)

## 🚀 Instalacja

### 1. Klonowanie/Setup projektu

```bash
cd C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper
```

### 2. Tworzenie Python virtual environment (rekomendowane)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalacja dependencies

```bash
# Z flag --break-system-packages (Cowork mode)
pip install -r requirements.txt --break-system-packages

# Lub normalnie
pip install -r requirements.txt
```

### 4. Konfiguracja zmiennych środowiskowych

Utwórz plik `.env` w głównym folderze:

```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
GMAIL_PASS=xxxx xxxx xxxx xxxx  # 16-znakowe App Password z Gmaila
```

Alternatywnie, ustaw zmienne środowiskowe systemowo (Windows):

```bash
setx SUPABASE_URL "https://your-project.supabase.co"
setx SUPABASE_KEY "your-key"
setx GMAIL_PASS "app-password"
```

### 5. Konfiguracja settings.json

Edytuj `config/settings.json` jeśli potrzebujesz zmienić delay'e, limity, itp.

```json
{
  "scraper": {
    "delay_min_sec": 7,        # Minimalna pauza między requestami
    "delay_max_sec": 10,       # Maksymalna pauza
    "max_requests_per_day": 50 # Daily limit
  }
}
```

## 🎯 Użycie

### Test lokalny (1 kod)

```bash
python scripts/scraper.py
```

Scraper automatycznie:
1. Pobierze listę kodów z Supabase (lub fallback)
2. Szuka wątków na elektorda.pl
3. Scrape'uje zawartość
4. Zapisuje do `/data/raw/` i `/data/parsed/`
5. Tworzy manifest w `/data/manifests/`
6. Loguje wszystko do `/logs/`

### Sprawdzanie logów

```bash
# Ostatnie 50 linii dzisiejszego logu
tail -50 logs/scraper_2026-07-12.log

# Windows (PowerShell)
Get-Content logs/scraper_2026-07-12.log -Tail 50
```

### Struktura danych po scraping'u

```
data/
├── raw/
│   └── 2026-07-12_E19.txt          (surowy tekst ze strony)
├── parsed/
│   └── 2026-07-12_E19.json         (sparsowany JSON)
└── manifests/
    └── manifest_2026-07-12.json    (podsumowanie sesji)
```

## 🔧 Troubleshooting

### ❌ "ConnectionError"
- Sprawdź internet
- Elektorda.pl może być down
- Czekaj 1 godzinę i spróbuj ponownie

### ❌ "403 Forbidden"
- Twój IP został tymczasowo zablokowany
- Zmień delay na 15-20 sekund w `settings.json`
- Czekaj 24 godziny

### ❌ "Brakuje settings.json"
- Utwórz plik `config/settings.json` na podstawie szablonu
- Lub skopiuj z `config/settings.json.example`

### ❌ "ModuleNotFoundError: No module named 'requests'"
```bash
pip install requests --break-system-packages
```

### ⚠️ "SUPABASE_URL not set"
- Ustaw zmienne środowiskowe (patrz punkt 4)
- Lub uruchom bez Supabase (fallback codes)

## 📅 Scheduling - Automatyczne uruchamianie

### GitHub Actions (REKOMENDOWANE - DARMOWE)

1. Push projekt do GitHub
2. Utwórz `.github/workflows/elektorda_scraper.yml`
3. Dodaj secrets w Settings → Secrets and variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `GMAIL_APP_PASSWORD`

```yaml
name: Elektorda Scraper

on:
  schedule:
    - cron: '0 2 * * *'  # Codziennie o 2:00 AM CET

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/scraper.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          GMAIL_PASS: ${{ secrets.GMAIL_APP_PASSWORD }}
```

### Windows Task Scheduler

1. Otwórz `Task Scheduler`
2. Create Basic Task
3. Name: "Elektorda Scraper"
4. Trigger: Daily at 2:00 AM
5. Action:
   ```
   Program: C:\Python311\python.exe
   Arguments: C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper\scripts\scraper.py
   ```

### Cron (Linux/Mac)

```bash
# Edytuj crontab
crontab -e

# Dodaj linię (2:00 AM codziennie)
0 2 * * * cd /home/user/pralkowcy/elektorda_scraper && python scripts/scraper.py
```

## 📊 Wynik sesji

Po uruchomieniu scraper'a zobaczysz:

```
======================================================================
ELEKTORDA SCRAPER START
Data: 2026-07-12
Projekt: Pralkowcy
======================================================================
✓ Supabase connected
📋 Kodów do sprawdzenia: 12
🔧 Processing: E19
  🔍 Searching for: E19
  ✓ Found URL: https://elektorda.pl/zmywarka-bosch-e19
  📄 Fetching thread...
  ✓ Saved raw: 2026-07-12_E19.txt
  ✓ Saved JSON: 2026-07-12_E19.json
✓ SUCCESS: E19
... (więcej kodów) ...
======================================================================
📊 PODSUMOWANIE:
  Żądań: 12
  Znalezione: 12
  Nie znalezione: 0
  Błędy: 0
======================================================================
✅ Scraping finished successfully!
```

## 📁 Struktura projektu

```
elektorda_scraper/
├── scripts/
│   ├── scraper.py          (< ty jesteś tutaj)
│   ├── analyzer.py         (Claude analysis - następnie)
│   ├── mailer.py           (Email + DB - następnie)
│   └── utils.py
├── config/
│   └── settings.json       (konfiguracja)
├── data/
│   ├── raw/                (surowe dane)
│   ├── parsed/             (JSON)
│   └── manifests/          (podsumowania)
├── reports/
│   ├── daily/              (codzienne raporty)
│   └── archive/
├── logs/                   (logi sesji)
└── README.md              (< tutaj)
```

## 📞 Support

- Logi: `logs/scraper_YYYY-MM-DD.log`
- Manifesty: `data/manifests/manifest_YYYY-MM-DD.json`
- Email: pralkowcy@gmail.com

## ⚖️ License

Pralkowcy - 2026
