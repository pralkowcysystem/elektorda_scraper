# 🔄 DEDUPLIKACJA + REVERSE CHRONOLOGICAL — Wyjaśnienie

**Problem:** Jak uniknąć zbierania tych samych wątków dwa razy?  
**Rozwiązanie:** Checkpoint system + reverse order (najnowsze najpierw)

---

## 📊 CO SIĘ DZIEJE (Wizualizacja)

### Dzień 1 (2026-07-14, noc 21:00-05:00)

```
ELEKTORDA MA:
[Wątek 5000 - najnowy 2026-07-14]
[Wątek 4999]
[Wątek 4998]
[Wątek 4997]
... (4000 starych wątków)
[Wątek 1 - najstary 2019-01-01]

SCRAPER ZBIERA (reverse):
1. Zaczyna od [Wątek 5000] ← najnowszy
2. Potem [Wątek 4999]
3. Potem [Wątek 4998]
... zbiera 800 wątków

ZAPISUJE CHECKPOINT:
/data/dedup/already_scraped_urls.json
{
  "urls": [url_5000, url_4999, ..., url_4201],
  "count": 800,
  "last_updated": "2026-07-14T05:30:00Z"
}
```

### Dzień 2 (2026-07-15, noc 21:00-05:00)

```
ELEKTORDA MA (nowe wątki pojawiły się):
[Wątek 5010 - najnowy 2026-07-15] ← NOWY
[Wątek 5009 - nowy 2026-07-15]   ← NOWY
[Wątek 5008 - nowy 2026-07-15]   ← NOWY
[Wątek 5007]
[Wątek 5006]
... 
[Wątek 5000] ← TE JUŻ MAMY!
[Wątek 4999]
... (stare, których nie chcemy)

SCRAPER ROBI:
1. Wczytuje checkpoint (już mamy 5000, 4999, ...)
2. Zaczyna od [Wątek 5010] (reverse, najnowsze)
3. Sprawdza: "Czy [Wątek 5010] już w checkpoint?" → NIE
4. Zbiera! ✅
5. Sprawdza: "Czy [Wątek 5009] już?" → NIE → Zbiera! ✅
6. Sprawdza: "Czy [Wątek 5008] już?" → NIE → Zbiera! ✅
7. Sprawdza: "Czy [Wątek 5007] już?" → NIE → Zbiera! ✅
...
8. Sprawdza: "Czy [Wątek 5000] już?" → TAK! → POMIŃ ❌

ZAPISUJE NOWY CHECKPOINT:
{
  "urls": [url_5010, url_5009, ..., url_4209],  (teraz 810 URLs)
  "count": 810,
  "last_updated": "2026-07-15T05:30:00Z"
}
```

---

## 🔧 JAK TO DZIAŁA TECHNICZNIE?

### 1. Wczytaj Checkpoint (już zebrane)

```python
already_scraped = load_already_scraped()
# Zwraca: {url_5000, url_4999, url_4998, ...}

logger.info(f"Deduplikacja: pomiń {len(already_scraped)} znanych URL-i")
# Output: Deduplikacja: pomiń 800 znanych URL-i
```

### 2. Posortuj Reverse (najnowsze najpierw)

```python
sorted_threads = sorted(
    raw_threads,
    key=lambda x: x.get('timestamp', ''),
    reverse=True  # ← REVERSE!
)

# Wynik:
# [Wątek 5010 - timestamp: 2026-07-15T14:30:00]  ← PIERWSZY!
# [Wątek 5009 - timestamp: 2026-07-15T13:45:00]
# [Wątek 5008 - timestamp: 2026-07-15T12:15:00]
# [Wątek 5007 - timestamp: 2026-07-15T11:00:00]
# [Wątek 5000 - timestamp: 2026-07-14T10:30:00]
# [Wątek 4999 - timestamp: 2026-07-14T09:15:00]  ← najmniejsze
```

### 3. Filtruj Duplikaty

```python
new_threads = []
for thread in sorted_threads:
    # Czy ten URL już zebraliśmy?
    if thread['url'] not in already_scraped:
        # Nie! Dodaj do listy
        new_threads.append(thread)
        
        # Ale nie zbieraj więcej niż MAX_THREADS_PER_NIGHT
        if len(new_threads) >= MAX_THREADS_PER_NIGHT:
            break  # Stop po 800 nowych

logger.info(f"Wątków do zebrania: {len(new_threads)} (nowych)")
# Output: Wątków do zebrania: 10 (nowych)
# (bo na dzień 2 pojawiło się tylko 10 nowych wątków!)
```

### 4. Zbierz + Zapisz Checkpoint

```python
for i, thread in enumerate(new_threads, 1):
    # ... zbierz wątek ...
    
    url = thread['url']
    processed_urls.add(url)  # ← Dodaj do checkpoint
    
    # Co 50 wątków, zapisz checkpoint (na wypadek przerwania)
    if i % 50 == 0:
        save_already_scraped(processed_urls)
        logger.info(f"Checkpoint: zapisano {len(processed_urls)} URL-i")

# Na koniec, zapisz finalny checkpoint
save_already_scraped(processed_urls)
logger.info(f"FINALNY CHECKPOINT: {len(processed_urls)} URL-i")
```

---

## 📂 STRUKTURA PLIKÓW

```
elektorda_scraper/
├── data/
│   ├── raw/
│   │   └── full_threads_with_content_2026-07-15.json  (nowe wątki)
│   ├── dedup/  ← NOWE!
│   │   └── already_scraped_urls.json  (pamiętaj co zebraliśmy)
│   └── parsed/
│       └── analyzed_with_solutions_2026-07-15.json
└── logs/
    └── scraper_v2_phase2_2026-07-15.log
```

### already_scraped_urls.json (struktura)

```json
{
  "urls": [
    "https://elektorda.pl/topic/12345",
    "https://elektorda.pl/topic/12346",
    "https://elektorda.pl/topic/12347",
    "..."
  ],
  "count": 850,
  "last_updated": "2026-07-15T05:30:00Z"
}
```

---

## 🎯 EFEKTY

### Dzień 1: Pełna historia zbierania

```
⏱️  02:00 → Scraper startuje
   • Brak checkpointa (pierwsza sesja)
   • Reverse: zaczyna od najnowszych
   • Zbiera 800 wątków (5000 → 4201)
   • Zapisuje checkpoint z 800 URL-i
   ✅ Koniec o 05:00

⏱️  08:00 → Analyzer
   • Analizuje 800 wątków
   • Tworzy SQL inserty
   ✅ Koniec o 08:15

✅ REZULTAT: 800 wątków, 500 SQL insertów
```

### Dzień 2: Inkrementalne (tylko nowe)

```
⏱️  02:00 → Scraper startuje
   • Wczytuje checkpoint (800 URL-i)
   • Pojawiło się 15 nowych wątków od wczoraj
   • Zbiera tylko 15 nowych (zajmuje 3-4 minuty!)
   • Zapisuje nowy checkpoint z 815 URL-i
   ✅ Koniec o 02:05 (szybko!)

⏱️  08:00 → Analyzer
   • Analizuje 15 nowych wątków
   • Tworzy SQL inserty (15 inserty)
   ✅ Koniec o 08:02

✅ REZULTAT: Tylko 15 nowych, bez duplikatów!
```

### Dzień 90 (skumulowany)

```
⏱️  02:00 → Scraper
   • Checkpoint zawiera 20,000+ URL-i
   • Codziennie zbiera ~20-50 nowych wątków
   • Nigdy nie duplikuje!
   ✅ Szybko (~2-5 minut)

📊 BAZA DANYCH:
   • 20,000 zebranych wątków
   • 0 duplikatów!
   • Przychody rosnące codziennie
```

---

## ⚠️ EDGE CASES

### Co się dzieje jeśli przerwiesz scraper o 03:00?

```
02:00 → Scraper startuje
03:00 → Zły weather, wyłączyłeś komputer (oops!)

Scraper ma CHECKPOINT:
- Zebrał 200 wątków
- Zapisał checkpoint co 50 wątków
- Ma ostatni checkpoint z 200 URL-i

04:00 → Włączasz komputer znowu
04:30 → Ręcznie uruchamiasz scraper

Scraper:
1. Wczytuje checkpoint (200 URL-i ze wczoraj)
2. Zaczyna od wątku 4800 (tam skończył)
3. Zbiera 600 więcej (już ma 200, potrzebuje 800)
4. BRAK DUPLIKATÓW! ✅
```

### Co się dzieje jeśli reverse order się nie zmieni?

```
Jeśli raw_threads nie mają timestamp:
  → Sortuję wg końca listy (ostatnie znalezione = najnowsze)
  → Reverse order i tak działa!
```

---

## 🎯 SUCCESS CRITERIA

✅ Deduplikacja działa jeśli:
- `already_scraped_urls.json` istnieje i rośnie
- Każdego dnia liczba wątków w logach się stabilizuje
- Żadny URL się nie pojawia dwa razy

✅ Reverse order działa jeśli:
- Log pokazuje "Sortowanie: najnowsze najpierw"
- Każdego dnia zbierane są NOWE wątki (z dzisiejszą datą)
- Nie ma wątków z 2019 roku (te są już w bazie)

---

## 📞 DEBUGGING

Jeśli coś nie działa, sprawdź log:

```bash
tail -50 logs/scraper_v2_phase2_2026-07-15.log

# Szukaj:
✓ "Deduplikacja: pomiń X znanych URL-i"    ← są stare
✓ "Wątków do zebrania: Y (nowych)"         ← jest Y nowych
✓ "Checkpoint: zapisano Z URL-i"          ← checkpoint działa
✓ "FINALNY CHECKPOINT: Z URL-i"           ← koniec sesji
```

Jeśli liczby rosną: **DZIAŁA!** 🎉
