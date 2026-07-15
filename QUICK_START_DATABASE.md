# ⚡ Quick Start — Database Setup (5 min)

**Szybki setup Supabase dla niecierpliwych**

---

## 🎯 W 5 Minut do Bazy Danych

### 1️⃣ Stwórz Projekt (2 min)

```
https://supabase.com → Sign up → New Project
Nazwa: pralkowcy-scraper
Password: zapisz gdzieś
```

⏳ Czekaj na załadowanie...

---

### 2️⃣ Uruchom SQL (1 min)

Skopiuj zawartość: `db/001_create_tables.sql`

```
Supabase → SQL Editor → New Query → Paste → Run
```

✅ Tabele gotowe!

---

### 3️⃣ Pobierz API Keys (1 min)

```
Settings → API
Skopiuj:
  SUPABASE_URL = https://xxxxx.supabase.co
  SUPABASE_KEY = eyJhbGc...
```

---

### 4️⃣ Ustaw Env Variables (1 min)

**PowerShell:**
```powershell
$env:SUPABASE_URL = "https://..."
$env:SUPABASE_KEY = "eyJ..."
```

**Lub .env file:**
```
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
```

---

### 5️⃣ Test (0 min)

```bash
python scripts/database.py
```

Output:
```
✓ Supabase client initialized
✓ Database module: OK
```

---

## 🎉 Gotowe!

```bash
python main.py
```

Zobaczysz:
```
✅ DATABASE SYNC SUCCESSFUL
```

---

## 📚 Więcej Info

- **SUPABASE_SETUP.md** — Pełny setup
- **DATABASE_INTEGRATION.md** — Jak to działa
- **scripts/database.py** — Kod

---

**To tyle! Baza już działa.** 🚀
