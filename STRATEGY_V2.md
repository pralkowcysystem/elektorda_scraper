# 🚀 STRATEGY V2: Pełne Dane + Rozsądne Delays + Offline Analiza

**Data:** 2026-07-14  
**Status:** ✅ Implementacja gotowa do testów  
**Cel:** Zbierać pełne dane (tytuł + zawartość) nocą, analizować offline dzień

---

## 📊 Przegląd Nowej Architektury

```
🌙 NOC (21:00 - 05:00)
├─ Phase 2 V2: SCRAPER
│  ├─ Delay: 10-12 sekund (SAFE!)
│  ├─ Target: 800 wątków (zamiast 2000)
│  ├─ Dane: TYTUŁ + PEŁNA ZAWARTOŚĆ
│  ├─ Format: JSON /data/raw/full_threads_with_content_YYYY-MM-DD.json
│  ├─ Czas: ~3-4 godziny (800 wątków * 11s + overhead)
│  ├─ Checkpoint: może wznowić jeśli przerwane
│  └─ Output: ~50MB JSON z rzeczywistą wiedzą

☀️ DZIEŃ (12:00)
├─ Phase 3: ANALYZER
│  ├─ Czyta: /data/raw/full_threads_with_content_YYYY-MM-DD.json (OFFLINE!)
│  ├─ Claude AI analizuje każdy wątek
│  ├─ Ekstraktuje: kod, przyczyna, rozwiązanie, części, koszt, trudność
│  ├─ Zero dodatkowego ruchu na elektordzie!
│  ├─ Deduplikuje (marca, model, kod, symptomy)
│  ├─ Generuje: SQL inserty do Supabase
│  ├─ Output: /db/inserts_YYYY-MM-DD.sql
│  └─ Czas: ~10-20 minut (w zależności od liczby wątków)

📊 MONITORING:
├─ scripts/monitor.py
├─ Raportuje postęp (% wątków, ETA, błędy)
├─ Health checks (jakość danych, errors)
└─ Codziennie o 14:00
```

---

## ✨ Czym się różni od V1?

| Aspekt | V1 (Stary) | V2 (Nowy) |
|--------|-----------|----------|
| **Dane na noc** | Tylko nagłówki (2000) | Nagłówki + zawartość (800) |
| **Delay** | 8-12s | 10-12s (bezpieczniej) |
| **Zawartość** | Brak | Pełna treść wątku (do 5KB) |
| **Analiza** | Tylko metadata | Claude analizuje tekst |
| **Rozwiązania** | Brak | ✅ Rzeczywiste kroki naprawy |
| **Części zamienne** | Brak | ✅ Numery OEM + zamienniki + koszt |
| **Ryzyko bana** | Średnie | Niskie (mniej requestów, dłuższe delays) |

---

## 🔧 Szczegół Techniczny

### Phase 2 V2 (scraper_v2_phase2.py)

**Co się zmieniło:**

```python
# STARO:
def fetch_thread_title(url):
    → Wchodzi w URL, wyciąga <h1>
    → Tylko tytuł

# NOWO:
def fetch_thread_full(url):
    → Wchodzi w URL
    → Wyciąga <h1> (tytuł)
    → Wyciąga ALL <div class="post"> (zawartość)
    → Zapisuje up to 20 postów, max 5KB tekstu
    → Zwraca {title, content, content_length}
```

**Parametry:**

```python
DELAY_MIN = 10  # Zwiększony z 8
DELAY_MAX = 12  # (bez zmian)
MAX_THREADS_PER_NIGHT = 800  # Redukacja z 2000
```

**Timeout:** ~3-4 godziny dla 800 wątków (800 × 11s ÷ 3600 ≈ 2.4h + overhead)

**Output:**

```json
{
  "url": "https://elektorda.pl/topic/...",
  "title": "Pralka Bosch E19 nie wiruje — rozwiązano",
  "content": "WĄTEK: Pralka Bosch...\n\n---\n\nODPOWIEDŹ 1: ...",
  "content_length": 2847,
  "brand": "Bosch",
  "device": "pralka",
  "error_code": "E19",
  "symptoms": ["nie wiruje"],
  "timestamp": "2026-07-14T02:05:30Z"
}
```

### Phase 3 (analyzer_claude.py) — NOWY

**Jak działa:**

1. Czyta `/data/raw/full_threads_with_content_YYYY-MM-DD.json` (OFFLINE)
2. Dla każdego wątku: wysyła do Claude AI (prompt w analyzer.py)
3. Claude ekstraktuje:
   - `kod_bledu` (E19, F04...)
   - `marka` (Bosch, LG...)
   - `urzadzenie` (pralka, zmywarka)
   - `symptomy` (lista)
   - `przyczyna` (root cause)
   - `rozwiazanie` (step-by-step)
   - `czesc_zamenna` (oryginalna + zamienniki + koszt)
   - `czas_naprawy_min` (liczba minut)
   - `poziom_trudnosci` (łatwy/średni/trudny)
   - `quality_score` (0.0-1.0)

4. Generuje SQL:
```sql
INSERT INTO kody_bledow 
(kod, marka, urzadzenie, symptomy, przyczyna, rozwiazanie, 
 poziom_trudnosci, czas_naprawy_min, quality_score, zrodlo) 
VALUES ('E19', 'Bosch', 'pralka', 'nie wiruje', 
        'Uszkodzony elektrozawór...', 'Wymień wkład A123456...', 
        'średni', 30, 0.92, 'elektorda.pl');
```

**Ryzyko dla Claude API:**

- Rate limit: 1000 requests/min (Phase 3 to ~50-100/min) ✅ OK
- Cost: ~$0.03/1000 tokens × 800 threads ≈ $0.24-1.00 / noc (tani)

---

## 📋 CHECKLIST WDROŻENIA

### ✅ Już zrobione

- [x] `scraper_v2_phase2.py` — zmieniony na `fetch_thread_full()`
- [x] `analyzer_claude.py` — nowy, analizuje zawartość
- [x] `monitor.py` — tracking postępu
- [x] Rozsądne delays (10-12s)
- [x] Redukcja wątków (800 zamiast 2000)

### 🔄 Do zrobienia przed Phase 1

- [ ] **Zweryfikuj kody** — uruchom `scraper_v2_phase2.py` na 10 wątkach TEST
  ```bash
  python elektorda_scraper/scraper_v2_phase2.py --test --limit 10
  ```

- [ ] **Test Claude API** — sprawdź czy `CLAUDE_API_KEY` działa
  ```bash
  python elektorda_scraper/scripts/analyzer_claude.py --test
  ```

- [ ] **Struktura folderów** — upewnij się że istnieją:
  ```
  /data/raw/
  /data/parsed/
  /logs/
  /reports/daily/
  /db/
  ```

- [ ] **Ustawienia env** — dodaj do .env lub settings.json:
  ```
  CLAUDE_API_KEY=sk-ant-...
  MAX_THREADS_PER_NIGHT=800
  DELAY_MIN=10
  DELAY_MAX=12
  ```

### 🚀 Uruchomienie

**Noc (21:00):**
```bash
cd elektorda_scraper
python scraper_v2_phase2.py
# Czeka ~3-4 godziny
# Output: data/raw/full_threads_with_content_2026-07-15.json (~50MB)
```

**Dzień (12:00):**
```bash
python scripts/analyzer_claude.py
# Czeka ~10-20 minut (zależy od API)
# Output: 
#   - parsed/analyzed_with_solutions_2026-07-15.json
#   - db/inserts_2026-07-15.sql
#   - reports/daily/analysis_report_2026-07-15.md
```

**Monitoring (14:00):**
```bash
python scripts/monitor.py --report 2026-07-15
# Wypisuje pełny raport systemu
```

---

## 🔍 MONITORING I JAKOŚĆ

### Co sprawdzać dzień po nocy (Phase 2)

```bash
# Otwórz log
tail -100 logs/scraper_v2_phase2_2026-07-15.log

# Szukaj:
# ✅ Sukcesy: X (powinno być ~700-800)
# ❌ Błędy: Y (powinno być < 50)
# 📊 Wskaźnik sukcesu: >85%
```

### Co sprawdzać po analizie (Phase 3)

```bash
# Otwórz log
tail -100 logs/analyzer_claude_2026-07-15.log

# Szukaj:
# ✅ Sukcesy: X (powinno być ~95% z Phase 2)
# 📊 Średnia jakość: >0.75
# 💾 SQL inserty: X (liczba INSERT'ów)
```

### Quality Metrics

```
✅ DOBRO:
  - Success rate Phase 2: >85%
  - Jakość Phase 3: >0.75
  - SQL inserty: >500
  - Błędy: <100

⚠️  OSTRZEŻENIE:
  - Success rate Phase 2: 70-85%
  - Jakość Phase 3: 0.50-0.75
  - SQL inserty: 200-500

❌ PROBLEM:
  - Success rate Phase 2: <70%
  - Jakość Phase 3: <0.50
  - SQL inserty: <200
  → Sprawdź logi, być może IP zablokowany lub zmiana HTML na elektordzie
```

---

## 🛡️ BEZPIECZEŃSTWO & RATE LIMITING

### Rozsądne Delays

```python
Delay: 10-12 sekund (random)
Dla 800 wątków: 800 × 11s = ~2.4 godzin
Requests/hour: 300 (czyli ~5/min)
Status: ✅ SAFE (elektróda nie powinna blokować)
```

### Detektowanie Bota

Jeśli elektróda zablokuje IP:
- Objawy: 403 Forbidden, timeout'y, "error 429"
- Rozwiązanie: zwiększ delay na 15-20s, zmień User-Agent
- Fallback: czekaj 24h, spróbuj z innego IP

### Rate Limit Supabase

Jeśli wgrywasz SQL:
- Max: ~1000 inserty/min (u nas to ~100 inserty/night)
- Status: ✅ OK

---

## 📞 TROUBLESHOOTING

### Phase 2: Błąd "ConnectionError"

```
❌ Przyczyna: Elektróda down lub brak internetu
✅ Rozwiązanie: 
  1. Sprawdź: ping elektorda.pl
  2. Czekaj 30 minut
  3. Uruchom ponownie (ma checkpoint system)
```

### Phase 2: Błąd "403 Forbidden"

```
❌ Przyczyna: IP został zablokowany
✅ Rozwiązanie:
  1. Czekaj 24 godziny
  2. Zwiększ delay na 15-20 sekund
  3. Zmień User-Agent w settings.json
```

### Phase 3: Błąd "Claude API error: 401"

```
❌ Przyczyna: CLAUDE_API_KEY invalid lub expired
✅ Rozwiązanie:
  1. Sprawdź: echo $CLAUDE_API_KEY
  2. Wygeneruj nowy key na console.anthropic.com
  3. Ustaw w .env lub settings.json
```

### Phase 3: Błąd "Timeout" w Claude API

```
❌ Przyczyna: Rate limit lub wolne API
✅ Rozwiązanie:
  1. Analyzer ma throttle: time.sleep(0.5) — OK
  2. Czekaj, spróbuj ponownie
  3. Zmniejsz batch size (ana tylko 100 wątków na raz)
```

---

## 📈 KOLEJNE KROKI (Phase 4+)

### Phase 4: Scheduled Automation

```yaml
# .github/workflows/elektorda_scraper.yml
schedule:
  - cron: '21 * * * *'  # Phase 2: każdego dnia o 21:00
  - cron: '12 * * * *'  # Phase 3: każdego dnia o 12:00
```

### Phase 5: Database Sync

```python
# mailer.py → wgrywanie SQL do Supabase
# + wysyłanie emaila z raportem
```

---

## 🎯 SUCCESS CRITERIA

✅ **Phase 2 sukcesem** jeśli:
- Zebrano ≥700 wątków (z 800 target)
- Quality score >85%
- Brak 403/rate limit errorsów

✅ **Phase 3 sukcesem** jeśli:
- Przeanalizowano ≥90% Phase 2
- Średnia jakość >0.75
- SQL inserty bez syntaksie errors

✅ **Całość sukcesem** jeśli:
- Baza ma >200 unikalnych kodów
- Każdy kod ma rozwiązanie (quality >0.75)
- Brak duplikatów (deduplikacja działa)

---

## 📞 PYTANIA?

Czytaj logi:
- Phase 2: `logs/scraper_v2_phase2_YYYY-MM-DD.log`
- Phase 3: `logs/analyzer_claude_YYYY-MM-DD.log`
- Monitor: uruchom `python scripts/monitor.py`

Tam zawsze jest prawda co się stało! 🔍
