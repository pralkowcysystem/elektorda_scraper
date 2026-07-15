#!/usr/bin/env python3
"""
Mock test scraper'a - symulacja pełnego output'u
Pokazuje co będzie w /data/raw/ i /data/parsed/ po scraping'u E19
"""

import json
from datetime import datetime
from pathlib import Path

print("=" * 70)
print("🧪 MOCK TEST: Symulacja scrapingu Bosch E19")
print("=" * 70)

# Symulowany surowy tekst ze strony elektorda.pl
RAW_CONTENT = """[METADATA]
kod: E19
title: Zmywarka Bosch Serie 4 miga E19 - nie przepływa woda
url: https://elektorda.pl/t/zmywarka-bosch-e19-nie-przeplywa-woda
scrape_date: 2026-07-12T02:15:30
posts_count: 12

[CONTENT]
USER: jankowalski_kraków
DATA: 2026-07-10 14:23
---
Cześć wszystkich! Mam zmywarkę Bosch Serie 4 (model SMS51E22EU).
Nagle zaczęła migać kod E19 i woda prawie nie przepływa.
Słychać czasami dziwne świszczące dźwięki od elektrozaworu.
Czy ktoś miał podobny problem? Co robić?

---
USER: tom_hydraulik_warszawa
DATA: 2026-07-10 15:45
---
To typowy kod dla problemu z elektrozaworem zasilającym (wlot wody).
E19 = No water inlet (brak wody na wlocie)

PRZYCZYNY:
1. Elektrozawór zasilający uszkodzony
2. Kabel do elektrozaworu przerwany
3. Przepływ wody blokowany (osad wapniowy)

ROZWIĄZANIE:
Elektronika jest OK, to problem mechaniczny.

Wymiana elektrozaworu:
- Zdejmij obudowę boczną (4 śrubki Phillips)
- Zdejmij panel główny (5 śrubków M5)
- Elektrozawór to jeden component na górze z lewej
- Części zamienne: A123456 (original Bosch) lub A789012 (aftermarket)
- Koszt części: original ~45zł, aftermarket ~28zł
- Czas naprawy: 30-45 minut dla początkującego

Najłatwiej: zamów serwis (150-200zł robocizna)

---
USER: robert_bosch_tech
DATA: 2026-07-10 16:10
---
+1 do tom_hydraulika

Ja miałem dokładnie to samo na swojej zmywarce Bosch.
Zdecydowałem się na wymianę części zamiennej (aftermarket).

Części:
- A789012 (perfect zamiennik)
- Kupiłem na Allegro za 22 zł
- Dostarczono w 2 dni

Wymiana:
- Proste jak się zna co robić
- Narzędzia: śrubokręt Phillips + klucz 10mm
- Nie trzeba odłączać przewodu wody (tylko elektry)
- Całość zajęła mi 25 minut

Status: ✓ Działa jak nowe! E19 gone!

Polecam aftermarket - zaoszczędzisz 20zł.

---
USER: maria_kraków
DATA: 2026-07-11 09:30
---
Dzięki za poradę! Właśnie zamówiłem część A789012 na Allegro.
Dostarczy się jutro. Chętnie bym to zrobił sam.

Pytanie: czy mogę znaleźć jakiś tutorial YouTube?

---
USER: tom_hydraulik_warszawa
DATA: 2026-07-11 10:15
---
@maria_kraków:
Nie ma dedykowanego tutoriala dla E19, ale wszystkie zmywarki mają podobną budowę.

Szukaj: "Bosch dishwasher inlet valve replacement"
Znajdziesz tam jak to zrobić.

Kluczowe kroki:
1. Wyłącz zasilanie
2. Zamknij zawór wody (główny zawór domu)
3. Zdejmij obudowę
4. Odłącz stary elektrozawór
5. Podłącz nowy
6. Testuj

W razie problemów - pisz tutaj!

---
USER: jankowalski_kraków
DATA: 2026-07-11 19:45
---
UPDATE: Zmówiłem część A789012, ma przyjść w piątek.
Podam feedback jak się zrobię wymianę.

Dziękuję wszystkim za szybką pomoc!

---
USER: jankowalski_kraków
DATA: 2026-07-12 08:10
---
SOLVED! ✓

Wymiana poszła super gładko!
Część A789012 przyszła, wszystko się pasowało.

Czas naprawy: 28 minut (z kawą przerwy :))
Koszt części: 22 zł
Zaoszczędzenie na serwisie: 150 zł

Zmywarka działa jak nowa!
Kod E19 jest historią.

Polecam tym którzy się boją - to naprawdę łatwe.
"""

# Symulowany sparsowany JSON
PARSED_JSON = {
    "kod_bledu": "E19",
    "model": "Bosch Serie 4 (SMS51E22EU)",
    "title": "Zmywarka Bosch Serie 4 miga E19 - nie przepływa woda",
    "url": "https://elektorda.pl/t/zmywarka-bosch-e19-nie-przeplywa-woda",
    "scrape_date": "2026-07-12T02:15:30Z",
    "status": "raw",
    "content_length": len(RAW_CONTENT),
    "posts_count": 9,
    "raw_file": "2026-07-12_E19.txt",
    "usterka": {
        "kod": "E19",
        "znaczenie": "No water inlet",
        "symptomy": [
            "Miga kod E19",
            "Woda prawie nie przepływa",
            "Dziwne świszczące dźwięki"
        ]
    },
    "przyczyny": [
        "Elektrozawór zasilający uszkodzony",
        "Kabel do elektrozaworu przerwany",
        "Przepływ wody blokowany (osad wapniowy)"
    ],
    "rozwiazanie": {
        "typ": "wymiana części",
        "kroki": [
            {
                "nr": 1,
                "opis": "Wyłącz zasilanie"
            },
            {
                "nr": 2,
                "opis": "Zamknij główny zawór wody"
            },
            {
                "nr": 3,
                "opis": "Zdejmij obudowę boczną (4 śrubki Phillips)"
            },
            {
                "nr": 4,
                "opis": "Zdejmij panel główny (5 śrubków M5)"
            },
            {
                "nr": 5,
                "opis": "Odłącz stary elektrozawór (brak konieczności odłączania przewodu wody)"
            },
            {
                "nr": 6,
                "opis": "Podłącz nowy elektrozawór"
            },
            {
                "nr": 7,
                "opis": "Zamontuj wszystko z powrotem"
            },
            {
                "nr": 8,
                "opis": "Testuj - otwórz zawór wody i uruchom zmywarkę"
            }
        ],
        "czas_minut": 30,
        "difficulty": "łatwy",
        "narzedzia": [
            "Śrubokręt Phillips",
            "Klucz 10mm"
        ]
    },
    "czesc_zamenna": {
        "oryginalna": {
            "numer": "A123456",
            "producent": "Bosch",
            "nazwa": "Elektrozawór zasilający",
            "koszt_pln": 45,
            "dostępność": "łatwo"
        },
        "zamienniki": [
            {
                "numer": "A789012",
                "producent": "Aftermarket (kompatybilny)",
                "nazwa": "Elektrozawór zasilający",
                "koszt_pln": 22,
                "dostępność": "Allegro",
                "rekomendacja": "POLECANE - działa idealnie, duże oszczędności"
            }
        ]
    },
    "feedback_użytkowników": {
        "łatwa_naprawa": True,
        "koszt_naprawy_serwis": 150,
        "koszt_części_zamienne": 22,
        "oszczędności": 128,
        "users_solved": 2
    },
    "quality_score": 0.95,
    "last_updated": "2026-07-12T08:10:00Z"
}

# Symulowany manifest
MANIFEST = {
    "date": "2026-07-12",
    "timestamp": "2026-07-12T02:30:00Z",
    "stats": {
        "requested": 1,
        "found": 1,
        "not_found": 0,
        "errors": 0
    },
    "codes_processed": ["E19"],
    "phase": "phase2_daily",
    "files": {
        "raw_count": 1,
        "parsed_count": 1
    }
}

# Wydruk
print("\n📁 STRUKTURA PLIKÓW PO SCRAPING'U:\n")

print("├── data/raw/2026-07-12_E19.txt")
print("│   └── Surowy tekst ze strony\n")
print("├── data/parsed/2026-07-12_E19.json")
print("│   └── Sparsowany JSON\n")
print("└── data/manifests/manifest_2026-07-12.json")
print("    └── Podsumowanie sesji\n")

print("=" * 70)
print("📝 ZAWARTOŚĆ: /data/raw/2026-07-12_E19.txt")
print("=" * 70)
print(RAW_CONTENT[:800])
print("\n... (pełna zawartość powyżej) ...\n")

print("=" * 70)
print("📊 ZAWARTOŚĆ: /data/parsed/2026-07-12_E19.json")
print("=" * 70)
print(json.dumps(PARSED_JSON, ensure_ascii=False, indent=2)[:1200])
print("\n... (pełna zawartość powyżej) ...\n")

print("=" * 70)
print("📋 ZAWARTOŚĆ: /data/manifests/manifest_2026-07-12.json")
print("=" * 70)
print(json.dumps(MANIFEST, ensure_ascii=False, indent=2))

print("\n" + "=" * 70)
print("✅ MOCK TEST ZAKOŃCZONY")
print("=" * 70)
print("""
CO SIĘ STAŁO:
✓ Znaleziono wątek dla E19 na elektorda.pl
✓ Pobrano zawartość (9 postów)
✓ Zapisano surowy tekst do /data/raw/
✓ Sparsowano JSON do /data/parsed/
✓ Utworzono manifest w /data/manifests/

W NASTĘPNYM KROKU:
1. analyzer.py przeczyta pliki z /data/raw/
2. Claude wyciągnę strukturę i analizy
3. Wygeneruje raport do /reports/daily/
4. Plikmailer.py wyśle mailem

TWÓJ NASTĘPNY KROK:
→ Uruchom scraper.py na SWOIM KOMPUTERZE
→ Będzie rzeczywiście pobierał z elektorda.pl
→ Struktura plików będzie dokładnie jak powyżej
""")

# Zapisz pliki do /tmp/ do weryfikacji
Path("/tmp/mock_E19_raw.txt").write_text(RAW_CONTENT, encoding='utf-8')
Path("/tmp/mock_E19_parsed.json").write_text(
    json.dumps(PARSED_JSON, ensure_ascii=False, indent=2),
    encoding='utf-8'
)
Path("/tmp/mock_manifest.json").write_text(
    json.dumps(MANIFEST, ensure_ascii=False, indent=2),
    encoding='utf-8'
)

print("\n💾 Pliki mock zapisane do /tmp/ (do weryfikacji)")
