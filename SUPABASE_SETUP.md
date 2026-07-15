# 📚 Supabase Setup Guide - Konfiguracja Bazy Danych

**Pralkowcy Scraper + Supabase PostgreSQL**

---

## 🎯 Cel

Przechowywanie wszystkich kodów błędów i logów scrapingu w Supabase (PostgreSQL w chmurze).

**Zalety:**
- ✅ Baza danych SQL (PostgreSQL)
- ✅ Darmowe 500MB storage
- ✅ Real-time API
- ✅ Backupy automatyczne
- ✅ Łatwy dostęp z aplikacji

---

## 📋 Warunki Wstępne

- ✅ Konto na GitHub (lub email)
- ✅ Plik `database.py` (już masz!)
- ✅ Biblioteka `supabase-py` (w requirements.txt)

---

## 🔧 KROK 1: Stwórz Projekt Supabase

### 1. Wejdź na https://supabase.com

### 2. Zaloguj się
   - GitHub login (lub email)

### 3. Stwórz nowy projekt
   - **"New Project"** → **"Create a new project"**
   - Nazwa: `pralkowcy-scraper`
   - Password: Zapisz gdzieś bezpiecznym miejscu! ⚠️
   - Region: Wybierz region bliski Tobie (np. Europe - EU-West)
   - Kliknij **"Create new project"**

⏳ Czekaj ~2 minuty na załadowanie...

---

## 🗄️ KROK 2: Utwórz Tabele

### A. Wejdź do SQL Editor

1. Po lewej stronie → **"SQL Editor"**
2. Kliknij **"+ New Query"**

### B. Copy-Paste SQL

Skopiuj zawartość pliku: `db/001_create_tables.sql`

```sql
-- Paste całą zawartość tutaj →
CREATE TABLE IF NOT EXISTS kody_bledow (...)
...
```

### C. Uruchom Query

Kliknij **"Run"** lub **Ctrl+Enter**

Powinna być wiadomość:
```
Success: 14 rows affected
```

✅ **Tabele zostały utworzone!**

---

## 🔑 KROK 3: Pobierz API Keys

### Lokalizacja: Settings → API

1. Po lewej stronie → **"Settings"**
2. Zakładka → **"API"**

### Skopiuj dwa klucze:

**`Project URL`** — Twój Supabase URL
```
https://xxxxxxxxxxxxx.supabase.co
```

**`anon public`** — Public API Key
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

(lub `service_role` secret jeśli chcesz pełny dostęp)

---

## 🌍 KROK 4: Ustaw Environment Variables

### Opcja A: Plik `.env` (rekomendowany)

Stwórz plik `.env` w folderze projektu:

```bash
C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper\.env
```

Zawartość:
```
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Opcja B: Zmienne systemowe (Windows)

Otwórz **PowerShell** lub **CMD**:

```powershell
$env:SUPABASE_URL = "https://xxxxxxxxxxxxx.supabase.co"
$env:SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Lub w **System Properties** (Zmienne Środowiskowe)

### Opcja C: settings.json

Dodaj do `config/settings.json`:

```json
{
  "supabase": {
    "url": "https://xxxxxxxxxxxxx.supabase.co",
    "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

I zmień `database.py`:
```python
# Line 79
supabase_url = config.get("supabase", {}).get("url")
supabase_key = config.get("supabase", {}).get("key")
```

---

## ✅ KROK 5: Test Połączenia

Uruchom test:

```bash
cd C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper
python scripts/database.py
```

Powinna się pojawić:
```
2026-07-12 17:00:00 - INFO - ✓ Supabase client initialized
✓ Database module: OK
Test complete.
```

✅ **Połączenie OK!**

---

## 📊 KROK 6: Weryfikacja Danych

### Wejdź do Table Editor

1. Po lewej stronie → **"Table Editor"**
2. Sprawdzaj tabele:
   - `kody_bledow` — (pusta, będzie po scrapingu)
   - `pytania_zadane` — (pusta, będzie po scrapingu)
   - `logi_scrapingu` — (pusta, będzie po scrapingu)

Jeśli tabele istnieją → **Setup kompletny!** ✅

---

## 🔒 Bezpieczeństwo

⚠️ **WAŻNE:**

### Nigdy nie commituj kluczy!

Dodaj do `.gitignore`:
```
.env
.env.local
config/supabase_key.txt
```

### API Keys — jakie wybrać?

| Klucz | Użycie | Bezpieczeństwo |
|-------|--------|---|
| **anon public** | Publiczny dostęp (z przeglądarki) | 🟡 Niskie — każdy może czytać |
| **service_role** | Serwer/skrypt (backend) | 🔴 Tajne — nie udostępniaj! |

**Dla scrapera:** Użyj `anon public` (jest w planie)

---

## 🧪 KROK 7: Pierwszy Test Insert

Stwórz plik `test_database.py`:

```python
from scripts.database import sync_to_database
import os

os.environ["SUPABASE_URL"] = "YOUR_URL"
os.environ["SUPABASE_KEY"] = "YOUR_KEY"

# Test data
test_data = [{
    "kod_bledu": "TEST1",
    "model": "Test Model",
    "usterka": {"przyczyna": "Test error"},
    "rozwiazanie": {"kroki": []},
    "czesc_zamenna": {"oryginalna": {"numer": "TEST", "koszt_pln": 0}},
    "quality_score": 0.5
}]

test_manifest = {
    "phase": "test",
    "codes": ["TEST1"],
    "stats": {
        "total_requests": 1,
        "found": 1,
        "not_found": 0,
        "errors": 0,
        "total_delay_time_sec": 0
    },
    "status": "success"
}

# Sync
result = sync_to_database(test_data, test_manifest)
print(f"✓ Result: {result}")

# Sprawdź w Supabase Table Editor
# Tabela: kody_bledow → powinna być 1 wiersz z kodem TEST1
```

Uruchom:
```bash
python test_database.py
```

Wejdź do Supabase → Table Editor → `kody_bledow`

Powinna być nowa linia z `kod: TEST1` ✅

---

## 📈 Monitoring i Statystyki

### Wejdź do Reports

1. Po lewej stronie → **"Reports"**
2. Możesz zobaczyć:
   - Ilość requestów
   - Storage użyty
   - Queries/dzień

---

## 🆘 Troubleshooting

### Problem: `SUPABASE_URL not set`

**Rozwiązanie:**
```bash
echo $env:SUPABASE_URL  # PowerShell
echo %SUPABASE_URL%     # CMD

# Jeśli puste, ustaw:
$env:SUPABASE_URL = "https://..."
```

### Problem: `Authentication failed`

**Rozwiązanie:**
- Sprawdź czy `SUPABASE_KEY` jest prawidłowy
- Skopiuj ponownie z Settings → API
- Sprawdź czy nie ma białych znaków na początku/końcu

### Problem: `Table does not exist`

**Rozwiązanie:**
- Sprawdź czy SQL query został uruchomiony bez błędów
- Wejdź do Table Editor i sprawdzaj czy tabele istnieją
- Uruchom SQL query ponownie

### Problem: `400 Bad Request`

**Rozwiązanie:**
- Sprawdzenie czy dane są w prawidłowym formacie JSON
- Czytaj logi: `tail -50 logs/database_*.log`
- Możliwe że kolumna typu nie zgadza się

---

## 📝 Logi

Wszystkie operacje bazy logowane w:

```
logs/database_YYYY-MM-DD.log
```

Sprawdzanie:
```bash
tail -50 logs/database_2026-07-12.log
```

---

## 🚀 Gotowe!

Teraz masz:
- ✅ Projekt Supabase
- ✅ Tabele PostgreSQL
- ✅ API keys
- ✅ Python module (database.py)

Następnie: Dodaj `sync_to_database()` do `main.py`!

---

## 📚 Dokumentacja

- [Supabase Docs](https://supabase.com/docs)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [supabase-py Library](https://github.com/supabase-community/supabase-py)

---

**Pytania?** Czytaj logi! 📋
