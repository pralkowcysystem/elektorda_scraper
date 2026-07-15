# 🔗 Integration Guide - Google Drive/Sheets do Scrapera

**Jak podpiąć gdrive_uploader.py do Twojego scrapera**

---

## 📌 Kroki Integracji

### Krok 1: Załaduj moduł

Na początku pliku `main.py` (lub `scheduler.py`):

```python
from scripts.gdrive_uploader import sync_to_google
import json
```

---

### Krok 2: Po Analyzers — Sync do Google

Po uruchomieniu `analyzer.py`, dodaj:

```python
# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("PRALKOWCY SCRAPER - FULL PIPELINE")
    logger.info("=" * 70)
    
    # PHASE 1: SCRAPING
    logger.info("\n📡 PHASE 1: SCRAPING")
    scraper_result = scraper.run()  # Pobiera dane
    
    if not scraper_result:
        logger.error("❌ Scraper failed - aborting pipeline")
        exit(1)
    
    # PHASE 2: ANALYSIS
    logger.info("\n🔍 PHASE 2: ANALYSIS")
    parsed_data, manifest = analyzer.run()  # Analizuje dane
    
    if not parsed_data:
        logger.warning("⚠️  No data to process - skipping Google sync")
        exit(0)
    
    # PHASE 3: GOOGLE DRIVE/SHEETS SYNC ← NOWA FAZA!
    logger.info("\n📊 PHASE 3: GOOGLE DRIVE/SHEETS SYNC")
    
    # Wczytaj konfigurację
    config_path = Path(__file__).parent / "config" / "settings.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    
    gdrive_config = config.get("google_drive", {})
    
    # Przygotuj liste plików do uploadowania
    today = datetime.now().strftime("%Y-%m-%d")
    data_dir = Path(__file__).parent / "data"
    
    report_files = []
    
    # Dodaj parsowane JSON'y
    parsed_dir = data_dir / "parsed"
    if parsed_dir.exists():
        report_files.extend(glob.glob(str(parsed_dir / f"{today}*.json")))
    
    # Dodaj report MD (jeśli istnieje)
    reports_dir = Path(__file__).parent / "reports" / "daily"
    if reports_dir.exists():
        findings_file = reports_dir / f"{today}_findings.md"
        if findings_file.exists():
            report_files.append(str(findings_file))
    
    # Synchronizuj do Google
    gdrive_result = sync_to_google(
        parsed_data=parsed_data,
        manifest=manifest,
        spreadsheet_id=gdrive_config.get("spreadsheet_id"),
        parent_folder_id=gdrive_config.get("parent_folder_id"),
        report_files=report_files
    )
    
    logger.info(f"✓ Google Sync Status: {gdrive_result['status']}")
    logger.info(f"  - Sheets: +{gdrive_result['sheets_added']} rows")
    logger.info(f"  - Drive: +{gdrive_result['files_uploaded']} files")
    
    if gdrive_result.get("errors"):
        logger.warning(f"⚠️  Errors: {gdrive_result['errors']}")
    
    # PHASE 4: DATABASE (opcjonalnie - Supabase)
    logger.info("\n💾 PHASE 4: DATABASE SYNC (OPTIONAL)")
    # ... tutaj dodaj database.py jeśli chcesz ...
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ PIPELINE COMPLETE")
    logger.info("=" * 70)
```

---

### Krok 3: Aktualizuj settings.json

W `config/settings.json` dodaj:

```json
{
  "scraper": {
    "delay_min_sec": 7,
    "delay_max_sec": 10,
    "max_requests_per_day": 50
  },
  
  "google_drive": {
    "parent_folder_id": "YOUR_FOLDER_ID",
    "spreadsheet_id": "YOUR_SHEET_ID",
    "create_daily_folders": true
  }
}
```

**Gdzie znaleźć:**
- **parent_folder_id** — ID folderu na Google Drive (z URL)
- **spreadsheet_id** — ID Google Sheets (z URL)

---

### Krok 4: Aktualizuj import'y

Dodaj na górze pliku:

```python
import glob
from datetime import datetime
from pathlib import Path
import json
```

---

## 📋 Pełny Przykład main.py

Jeśli nie masz jeszcze `main.py`, tutaj całą strukturę:

```python
#!/usr/bin/env python3
"""
Pralkowcy Scraper - Main Orchestrator
Koordynuje: scraper → analyzer → gdrive/sheets → database
"""

import json
import glob
import logging
from pathlib import Path
from datetime import datetime

# Importy z własnych modulów
from scripts.scraper import run as run_scraper
from scripts.analyzer import run as run_analyzer
from scripts.gdrive_uploader import sync_to_google

# =============================================================================
# LOGGING
# =============================================================================

def setup_logger():
    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)
    
    log_file = Path(__file__).parent / "logs" / f"main_{datetime.now().strftime('%Y-%m-%d')}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    fh = logging.FileHandler(log_file, encoding='utf-8')
    ch = logging.StreamHandler()
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_logger()

# =============================================================================
# MAIN PIPELINE
# =============================================================================

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("🚀 PRALKOWCY SCRAPER - FULL PIPELINE START")
    logger.info("=" * 70)
    
    # PHASE 1: SCRAPING
    logger.info("\n📡 PHASE 1: SCRAPING FROM ELEKTORDA")
    scraper_result = run_scraper()
    
    if not scraper_result:
        logger.error("❌ Scraper failed")
        exit(1)
    
    # PHASE 2: ANALYSIS
    logger.info("\n🔍 PHASE 2: ANALYZING DATA WITH CLAUDE")
    parsed_data, manifest = run_analyzer()
    
    if not parsed_data:
        logger.warning("⚠️  No parsed data")
        exit(0)
    
    # PHASE 3: GOOGLE SYNC
    logger.info("\n📊 PHASE 3: UPLOADING TO GOOGLE DRIVE/SHEETS")
    
    config_path = Path(__file__).parent / "config" / "settings.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    
    gdrive_config = config.get("google_drive", {})
    
    # Przygotuj pliki
    today = datetime.now().strftime("%Y-%m-%d")
    data_dir = Path(__file__).parent / "data"
    report_files = list(glob.glob(str(data_dir / "parsed" / f"{today}*.json")))
    
    # Sync
    result = sync_to_google(
        parsed_data=parsed_data,
        manifest=manifest,
        spreadsheet_id=gdrive_config.get("spreadsheet_id"),
        parent_folder_id=gdrive_config.get("parent_folder_id"),
        report_files=report_files
    )
    
    logger.info(f"✓ Status: {result['status']}")
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ PIPELINE COMPLETE")
    logger.info("=" * 70)
```

---

## 🧪 Test Całej Pipeline

```bash
cd C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper

# Test całej pipeline'u
python main.py
```

Powinna się pojawić:
```
==========================================
🚀 PRALKOWCY SCRAPER - FULL PIPELINE START
==========================================

📡 PHASE 1: SCRAPING FROM ELEKTORDA
✓ Scraper completed: 12 requests

🔍 PHASE 2: ANALYZING DATA WITH CLAUDE
✓ Analyzed: 12 codes

📊 PHASE 3: UPLOADING TO GOOGLE DRIVE/SHEETS
✓ Google services initialized successfully
✓ Added 12 rows to Sheets
✓ Created folder: Raport_2026-07-12
✓ Uploaded: 2026-07-12_E19.json
...

✅ PIPELINE COMPLETE
```

---

## 🔄 Automatyczne Uruchamianie (GitHub Actions)

Jeśli chcesz automatyzacji, zmodyfikuj `.github/workflows/elektorda_scraper.yml`:

```yaml
name: Elektorda Scraper + Google Sync

on:
  schedule:
    - cron: '0 2 * * *'  # Codziennie o 2:00 AM

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
      
      - name: Run full pipeline
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: |
          cd elektorda_scraper
          python main.py
      
      - name: Commit results
        run: |
          git config user.email "bot@pralkowcy.pl"
          git config user.name "Pralkowcy Bot"
          git add logs/ data/ reports/
          git commit -m "✓ Scrape + Google Sync $(date +%Y-%m-%d)" || true
          git push
```

---

## ✅ Checklist Integracji

- [ ] Umieszczono `pralkowcy-scraper-*.json` w `config/`
- [ ] Folder na Google Drive udostępniony Service Accountowi
- [ ] `settings.json` zawiera `google_drive` config z ID'ami
- [ ] Zainstalowano biblioteki: `pip install -r requirements.txt --break-system-packages`
- [ ] Dodano import'y w `main.py`
- [ ] Dodano `sync_to_google()` call w pipeline'u
- [ ] Test `python main.py` się powiedzie
- [ ] Logi się pojawią w `logs/gdrive_*.log`
- [ ] Folder na Drive ma nowe pliki

---

## 🆘 Problemy?

Sprawdź:
1. Logi: `tail -50 logs/gdrive_*.log`
2. Credentials: czy plik jest w `config/`?
3. Uprawnienia: czy folder na Drive jest udostępniony?
4. Config: czy `settings.json` ma prawidłowe ID'y?

---

**Gotowe!** Twój scraper teraz uploaduje wszystko do Google Drive! 🎉
