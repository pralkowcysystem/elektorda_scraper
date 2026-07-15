# 📚 Google Drive & Sheets Integration - Setup Guide

**Pralkowcy Scraper + Google Drive/Sheets**

---

## 🎯 Cel

Automatyczne uploadowanie wyników scrapingu do:
- ✅ **Google Sheets** — tabelaryczne raporty (bieżący dostęp)
- ✅ **Google Drive** — archiwum plików JSON + raporty HTML

---

## 📋 Warunki Wstępne

Masz już:
- ✅ Google Cloud Project (`pralkowcy-scraper`)
- ✅ Włączone API: Google Sheets API + Google Drive API
- ✅ Service Account (`pralkowcy-scraper`)
- ✅ Pobrany plik credentials.json

---

## 🔧 Krok 1: Umieszczenie credentials.json

### Lokalizacja pliku:

```
C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper\config\
├── settings.json
└── pralkowcy-scraper-04aaed542e48.json  ← credentials (już tam!)
```

**Plik powinien być w folderze `config/`** — już tam umieściłeś! ✓

---

## 🗂️ Krok 2: Przygotowanie Google Drive

### Opcja A: Udostępnij istniejący folder

1. **Otwórz Google Drive** → https://drive.google.com

2. **Stwórz folder** (jeśli go jeszcze nie masz):
   - Nazwa: `Pralkowcy_Raporty` (lub dowolna)

3. **Uzyskaj ID folderu** z URL:
   ```
   https://drive.google.com/drive/folders/[FOLDER_ID]
   ```

4. **Udostępnij folder** Service Accountowi:
   - Kliknij PPM na folder → **Udostępnij**
   - Email: `pralkowcy-scraper@pralkowcy-scraper.iam.gserviceaccount.com`
   - Rola: **Edytor** (Editor)
   - Wyślij zaproszenie

---

## 🔑 Krok 3: Konfiguracja settings.json

Dodaj do `config/settings.json` nową sekcję:

```json
{
  "scraper": { ... },
  "google_drive": {
    "parent_folder_id": "YOUR_FOLDER_ID",
    "spreadsheet_id": "YOUR_SHEET_ID",
    "create_daily_folders": true
  }
}
```

### Gdzie znaleźć ID?

**Folder ID:**
```
https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J
                                         ^^^^^^^^^^^^^^^^^^^^^^
```

**Spreadsheet ID:**
```
https://docs.google.com/spreadsheets/d/1A2B3C4D5E6F7G8H9I0J/edit
                                       ^^^^^^^^^^^^^^^^^^^^^^
```

---

## 💻 Krok 4: Instalacja bibliotek

```bash
cd C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper

pip install -r requirements.txt --break-system-packages
```

Będą zainstalowane:
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `google-api-python-client`

---

## 📝 Krok 5: Integracja z main.py

W głównym orchestratorze (`main.py` lub `scheduler.py`) dodaj:

```python
from scripts.gdrive_uploader import sync_to_google
import json

# Po analizie danych (po analyzer.py)
if __name__ == "__main__":
    # ... scraper.run() ...
    # ... parsed_data, manifest = analyzer.run() ...
    
    # Wczytaj konfigurację
    with open("config/settings.json") as f:
        config = json.load(f)
    
    gdrive_config = config.get("google_drive", {})
    
    # Lista plików do uploadowania
    report_files = [
        "reports/daily/2026-07-12_findings.md",  # Przykład
        "data/parsed/2026-07-12_E19.json",
        # ... dodaj inne
    ]
    
    # Sync do Google Drive/Sheets
    result = sync_to_google(
        parsed_data=parsed_data,
        manifest=manifest,
        spreadsheet_id=gdrive_config.get("spreadsheet_id"),
        parent_folder_id=gdrive_config.get("parent_folder_id"),
        report_files=report_files
    )
    
    print(f"✓ Google Sync: {result['status']}")
```

---

## 🧪 Krok 6: Test

**Test modułu gdrive_uploader:**

```bash
cd C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper
python scripts/gdrive_uploader.py
```

Powinna się pojawić wiadomość:
```
2026-07-12 16:00:00 - INFO - ✓ Google services initialized successfully
✓ Sheets service: OK
✓ Drive service: OK
Test complete.
```

---

## 📊 Struktura na Google Drive

Po uruchomieniu scraper'a struktura będzie wyglądać:

```
📁 Pralkowcy_Raporty (parent_folder_id)
├── 📊 Raporty (Sheets) ← wiersze trafiają tutaj
│   └── Kolumny: Data | Kod | Model | Usterka | Rozwiązanie | Koszt | Score
│
└── 📁 Archiwa/
    ├── 📁 Raport_2026-07-12/
    │   ├── 2026-07-12_E19.json
    │   ├── 2026-07-12_F04.json
    │   └── manifest.json
    │
    └── 📁 Raport_2026-07-13/
        └── ...
```

---

## ⚠️ Troubleshooting

### Problem: `Credentials file not found`

**Rozwiązanie:**
- Sprawdzić czy `pralkowcy-scraper-04aaed542e48.json` jest w `config/`
- Lub zmienić ścieżkę w `gdrive_uploader.py` line 32

### Problem: `403 Forbidden` przy uploadzie

**Rozwiązanie:**
- Folder nie jest udostępniony Service Accountowi
- Sprawdzić uprawnienia w Google Drive
- Udostępnić folder na emailu: `pralkowcy-scraper@pralkowcy-scraper.iam.gserviceaccount.com`

### Problem: `Spreadsheet not found`

**Rozwiązanie:**
- Sprawdzić `spreadsheet_id` w `settings.json`
- Sprawdzić czy Sheets jest udostępniony Service Accountowi

### Logowanie

Logi są w: `logs/gdrive_YYYY-MM-DD.log`

```bash
tail -50 logs/gdrive_2026-07-12.log
```

---

## 📖 Dokumentacja API

- [Google Sheets API](https://developers.google.com/sheets/api)
- [Google Drive API](https://developers.google.com/drive/api)
- [Service Account Auth](https://cloud.google.com/docs/authentication/end-user)

---

## 🔒 Bezpieczeństwo

⚠️ **WAŻNE:**
- **Nigdy** nie commituj `pralkowcy-scraper-04aaed542e48.json` do Git'a
- Dodaj do `.gitignore`:
  ```
  config/pralkowcy-scraper-*.json
  config/credentials.json
  ```
- Klucz ma dostęp do Twojego Drive — chroń go!

---

## 🎉 Koniec!

Gotowe! Scraper teraz:
- 📤 Uploaduje pliki do Google Drive
- 📊 Dodaje wiersze do Google Sheets
- 📁 Organizuje raporty w folderach dziennych
- 📝 Loguje wszystkie operacje

**Powodzenia!** 🚀
