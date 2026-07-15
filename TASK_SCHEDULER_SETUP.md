# 🕐 WINDOWS TASK SCHEDULER — Setup Instrukcja

**Cel:** Uruchomić Scraper o 02:00 i Analyzer o 08:00 AUTOMATYCZNIE każdego dnia.

---

## KROK 1: Znajdź Python

Otwórz **PowerShell** i wpisz:

```powershell
python --version
where python
```

**Output powinien być:**
```
Python 3.11.x
C:\Users\Lenovo\AppData\Local\Programs\Python\Python311\python.exe
```

**Zapamiętaj tę ścieżkę!** (będzie PYTHON_PATH)

---

## KROK 2: Otwórz Task Scheduler

**Windows Start (klawisz Windows) → wpisz:**

```
Task Scheduler
```

**Kliknij:** "Task Scheduler" → Enter

---

## KROK 3: SCRAPER — 02:00 (NOCA)

### A) Create Task

W lewym panelu → **Task Scheduler Library** (kliknij)

Prawy panel → **Create Basic Task...**

### B) General Tab

```
Name: Pralkowcy Scraper - 02:00 (Noc)
Description: Zbiera dane z elektorda.pl automatycznie o 2:00 AM
☑️ Run with highest privileges
```

**Next →**

### C) Triggers Tab

**New...**

```
Begin the task: On a schedule
Settings:
  ☑️ Daily
  Start: 02:00:00 (ustaw godzinę!)
  Recur every: 1 day
```

**OK → Next →**

### D) Actions Tab

**New...**

```
Action: Start a program

Program/script:
  C:\Users\Lenovo\AppData\Local\Programs\Python\Python311\python.exe
  
  (wklej tę ścieżkę z KROKU 1!)

Add arguments (optional):
  C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper\scraper_v2_phase2.py

Start in (optional):
  C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper
```

**OK → Next →**

### E) Conditions Tab

Domyślne ustawienia → **Next →**

### F) Settings Tab

```
☑️ Allow task to be run on demand
☑️ If the task fails, restart every: 5 minutes (try 3 times)
☑️ If the running task does not end when requested, force it to close
⚠️ Do not start a new instance if an existing instance is running
```

**OK → Finish**

---

## KROK 4: ANALYZER — 08:00 (RANO)

**Powtórz KROKI 2-3, ale zmień:**

```
Name: Pralkowcy Analyzer - 08:00 (Ranek)
Description: Analizuje dane ze scraiera

Trigger:
  Daily o 08:00:00

Program/script:
  C:\Users\Lenovo\AppData\Local\Programs\Python\Python311\python.exe

Add arguments:
  C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper\scripts\analyzer_claude.py

Start in:
  C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper
```

---

## ✅ SPRAWDZENIE

### Test 1: Task Scheduler pokazuje zadania

```
Task Scheduler Library
→ Powinno być 2 zadania:
  ✓ Pralkowcy Scraper - 02:00 (Noc)
  ✓ Pralkowcy Analyzer - 08:00 (Ranek)
```

### Test 2: Uruchom ręcznie

**Kliknij na zadanie** → Prawy klik → **Run**

Powinno się uruchomić natychmiast (terminal się pojawi, będzie zbierać/analizować)

### Test 3: Sprawdź logi

```
cd C:\Users\Lenovo\Claude\Projects\prakowcy\elektorda_scraper

# Logi scraper'a
cat logs/scraper_v2_phase2_2026-07-15.log

# Logi analyzer'a
cat logs/analyzer_claude_2026-07-15.log
```

---

## 🔧 TROUBLESHOOTING

### Problem: "Program not found"

**Przyczyna:** Zła ścieżka do python.exe

**Rozwiązanie:**
```powershell
# Terminal → sprawdź dokładną ścieżkę
where python

# Wklej dokładną ścieżkę do Task Scheduler
```

### Problem: "Access Denied"

**Przyczyna:** Brak uprawnień

**Rozwiązanie:**
```
Task Scheduler → Właściwości zadania
  ✓ Run with highest privileges
  → OK
```

### Problem: Zadanie nie uruchamia się o 02:00

**Przyczyna:** Komputer jest wyłączony!

**Rozwiązanie:**
```
Ustaw komputer aby nie zasypiał o nocy:
  Windows Settings → Power & sleep
  → Set to: Never
```

### Problem: "Python module not found" (requests, bs4)

**Przyczyna:** Brakuje bibliotek

**Rozwiązanie:**
```powershell
# Terminal (jako Administrator)
pip install requests beautifulsoup4 pandas anthropic
```

---

## 📋 HARMONOGRAM — CZEGO OCZEKIWAĆ

```
02:00 AM → Scraper uruchamia się
├─ Zbiera 800 wątków
├─ Zapis: /data/raw/full_threads_with_content_2026-07-15.json
├─ Czas: ~3-4 godziny
└─ Terminal zamyka się

08:00 AM → Analyzer uruchamia się
├─ Czyta: /data/raw/full_threads_with_content_2026-07-15.json
├─ Claude analizuje
├─ Zapis: /db/inserts_2026-07-15.sql
├─ Czas: ~10-20 minut
└─ Terminal zamyka się

14:00 → Monitor check (opcjonalnie ręczny)
python scripts/monitor.py --report 2026-07-15
```

---

## 🎯 SUCCESS

✅ Jeśli widzisz:
```
logs/scraper_v2_phase2_2026-07-15.log:
  ✅ Sukcesy: 750
  📊 Wskaźnik sukcesu: 93.7%

logs/analyzer_claude_2026-07-15.log:
  ✅ Sukcesy: 720
  💾 SQL inserty: 500
```

**Gratulacje! System działa! 🚀**

---

## 📞 PYTANIA?

Sprawdzaj logi:
- `/logs/scraper_v2_phase2_*.log`
- `/logs/analyzer_claude_*.log`

Tam zawsze jest pravda co się stało!
