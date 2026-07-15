#!/usr/bin/env python3
"""
SCRAPER V2 - ZBIERANIE BAZY WIEDZY
Zbiera wątki z elektrody.pl, parsuje dane, deduplikuje
Cel: Zgromadzić czystą bazę problemów dla Pralkowcy

Author: Claude (Pralkowcy)
Date: 2026-07-14
"""

import os
import sys
import json
import time
import random
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
import pandas as pd

# =============================================================================
# KONFIGURACJA
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PARSED_DIR = DATA_DIR / "parsed"
LOGS_DIR = PROJECT_ROOT / "logs"

for d in [DATA_DIR, RAW_DIR, PARSED_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Logger
def setup_logger():
    logger = logging.getLogger("scraper_v2")
    logger.setLevel(logging.DEBUG)

    log_file = LOGS_DIR / f"scraper_v2_{datetime.now().strftime('%Y-%m-%d')}.log"
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = setup_logger()

# Słowa kluczowe do szukania
SEARCH_KEYWORDS = [
    "pralka",
    "zmywarka",
    "suszarka",
    "piekarnik",
]

MAX_PAGES_PER_KEYWORD = 3  # Dla testu
BASE_URL = "https://elektroda.pl"
TIMEOUT = 30
DELAY_MIN = 8
DELAY_MAX = 12

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Checkpoint system
CHECKPOINT_FILE = DATA_DIR / "checkpoint_scraper_v2.json"
CHECKPOINT_INTERVAL = 50  # Zapisuj co 50 wątków

# =============================================================================
# PARSING HELPERS
# =============================================================================

BRANDS = [
    'Bosch', 'Siemens', 'LG', 'Samsung', 'Whirlpool', 'Ariston', 'Indesit',
    'Electrolux', 'AEG', 'Zanussi', 'Beko', 'Candy', 'Hotpoint', 'Miele',
    'IKEA', 'Privileg', 'Constructa', 'Neff', 'Bauknecht', 'Gorenje', 'Vestel'
]

DEVICES = {
    'pralka': ['pralka', 'washer', 'washing'],
    'zmywarka': ['zmywarka', 'dishwasher', 'zmywarek'],
    'suszarka': ['suszarka', 'dryer'],
    'piekarnik': ['piekarnik', 'oven', 'piekarn'],
}

SYMPTOMS = {
    'nie wiruje': ['nie wiruje', 'nie obraca', 'bęben nie obraca'],
    'bierze wodę': ['bierze wodę', 'pobiera wodę', 'nie bierze wody'],
    'nie grzeje': ['nie grzeje', 'zimna woda'],
    'przecieka': ['przecieka', 'wycieka woda'],
    'hałas': ['hałas', 'rzęzi', 'śrinka'],
    'nie otwiera': ['nie otwiera drzwi', 'zablokowane drzwi'],
    'błąd wyświetlacza': ['błąd', 'kod', 'error'],
}

def extract_brand(title: str) -> Optional[str]:
    """Ekstraktuj markę z tytułu"""
    for brand in BRANDS:
        if brand.lower() in title.lower():
            return brand
    return None

def extract_device(title: str) -> Optional[str]:
    """Ekstraktuj typ urządzenia"""
    for device, keywords in DEVICES.items():
        for keyword in keywords:
            if keyword.lower() in title.lower():
                return device
    return None

def extract_error_code(title: str) -> Optional[str]:
    """Ekstraktuj kod błędu"""
    patterns = [
        r'\b[EeFfAaCcDdHh]\-?\d{1,3}\b',
        r'(?:Error|Błąd|error|błąd)\s*[EeFfAaCcDdHh]?\-?\d{1,3}',
    ]

    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None

def extract_symptoms(title: str) -> List[str]:
    """Ekstraktuj symptomy"""
    symptoms = []
    for symptom, keywords in SYMPTOMS.items():
        for keyword in keywords:
            if keyword.lower() in title.lower():
                symptoms.append(symptom)
                break
    return symptoms

def parse_title(title: str, keyword: str, url: str) -> Dict:
    """Parsuj pełny tytuł"""
    return {
        'title': title,
        'keyword': keyword,
        'url': url,
        'brand': extract_brand(title),
        'device': extract_device(title),
        'error_code': extract_error_code(title),
        'symptoms': extract_symptoms(title),
        'timestamp': datetime.now().isoformat()
    }

# =============================================================================
# CHECKPOINT SYSTEM
# =============================================================================

def load_checkpoint() -> Dict:
    """Załaduj checkpoint jeśli istnieje"""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        logger.info(f"✅ Wznawiam od checkpoint: {checkpoint['timestamp']}")
        logger.info(f"   Zebrane wątki: {len(checkpoint['threads'])}")
        logger.info(f"   Ostatnie słowo: {checkpoint['last_keyword']}")
        return checkpoint
    return None

def save_checkpoint(threads: List[Dict], keyword: str, page: int):
    """Zapisz checkpoint"""
    checkpoint = {
        'timestamp': datetime.now().isoformat(),
        'threads': threads,
        'last_keyword': keyword,
        'last_page': page,
        'total_count': len(threads)
    }
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)

def delete_checkpoint():
    """Usuń checkpoint (gdy skończymy)"""
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        logger.info("🗑️  Checkpoint usunięty")

# =============================================================================
# SCRAPER
# =============================================================================

def scrape_keyword(keyword: str, max_pages: int = 3) -> List[Dict]:
    """Scrape'uj wszystkie wątki dla danego słowa kluczowego"""
    results = []

    logger.info(f"\n🔍 Szukam: '{keyword}'")

    for page in range(1, max_pages + 1):
        try:
            search_url = f"{BASE_URL}/rtvforum/find.php?q={quote(keyword)}&p={page}"
            logger.debug(f"  Strona {page}: {search_url}")

            response = requests.get(
                search_url,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Szukaj wszystkich linków do wątków
            thread_links = soup.find_all('a', href=re.compile(r'topic\d+'))

            page_count = 0
            for link in thread_links:
                title = link.get_text(strip=True)
                href = link.get('href', '')

                # Filtruj: min 10 znaków, nie URL
                if len(title) < 10 or title.startswith('http'):
                    continue

                if 'topic' not in href:
                    continue

                url = href if href.startswith('http') else BASE_URL + href
                parsed = parse_title(title, keyword, url)
                results.append(parsed)
                page_count += 1

            logger.info(f"  ✅ Strona {page}: {page_count} wątków")

            # Delay bezpieczeństwa
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            time.sleep(delay)

        except Exception as e:
            logger.error(f"  ❌ Błąd na stronie {page}: {e}")
            continue

    logger.info(f"📊 '{keyword}': znaleziono {len(results)} wątków")
    return results

def scrape_all() -> List[Dict]:
    """Scrape'uj wszystkie słowa kluczowe (z checkpoint'ami)"""

    # Sprawdź checkpoint
    checkpoint = load_checkpoint()
    if checkpoint:
        all_threads = checkpoint['threads']
        start_keyword_idx = SEARCH_KEYWORDS.index(checkpoint['last_keyword'])
        # Pomiń już zebrane słowa
        keywords_to_scrape = SEARCH_KEYWORDS[start_keyword_idx:]
    else:
        all_threads = []
        keywords_to_scrape = SEARCH_KEYWORDS

    logger.info("=" * 80)
    logger.info("SCRAPER V2 - START")
    logger.info(f"Słowa kluczowe: {len(keywords_to_scrape)}")
    logger.info(f"Stron na słowo: {MAX_PAGES_PER_KEYWORD}")
    if checkpoint:
        logger.info(f"🔄 WZNAWIANIE - już zebrane: {len(all_threads)} wątków")
    logger.info("=" * 80)

    for keyword in keywords_to_scrape:
        try:
            threads = scrape_keyword(keyword, MAX_PAGES_PER_KEYWORD)
            all_threads.extend(threads)

            logger.info(f"Razem dotychczas: {len(all_threads)} wątków\n")

            # Zapisz checkpoint co CHECKPOINT_INTERVAL wątków
            if len(all_threads) % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(all_threads, keyword, MAX_PAGES_PER_KEYWORD)
                logger.info(f"💾 Checkpoint zapisany ({len(all_threads)} wątków)")

        except KeyboardInterrupt:
            logger.warning("⚠️  Przerwano przez użytkownika")
            save_checkpoint(all_threads, keyword, MAX_PAGES_PER_KEYWORD)
            logger.info("💾 Checkpoint zapisany - można wznowić później")
            sys.exit(0)
        except Exception as e:
            logger.error(f"❌ Błąd dla '{keyword}': {e}")
            save_checkpoint(all_threads, keyword, MAX_PAGES_PER_KEYWORD)
            continue

    return all_threads

# =============================================================================
# DEDUPLIKACJA
# =============================================================================

def deduplicate(threads: List[Dict]) -> Dict[tuple, Dict]:
    """Deduplikuj wątki po (brand, device, error_code, symptom)"""
    logger.info("\n" + "=" * 80)
    logger.info("DEDUPLIKACJA")
    logger.info("=" * 80)

    dedup_map = {}

    for thread in threads:
        # Klucz: (brand, device, error_code, symptoms)
        key = (
            thread['brand'] or 'unknown',
            thread['device'] or 'unknown',
            thread['error_code'] or 'unknown',
            tuple(sorted(thread['symptoms'])) or ('unknown',)
        )

        if key not in dedup_map:
            dedup_map[key] = {
                'brand': thread['brand'],
                'device': thread['device'],
                'error_code': thread['error_code'],
                'symptoms': thread['symptoms'],
                'count': 0,
                'urls': [],
                'first_title': thread['title'],
                'last_updated': thread['timestamp']
            }

        dedup_map[key]['count'] += 1
        dedup_map[key]['urls'].append(thread['url'])
        dedup_map[key]['last_updated'] = thread['timestamp']

    logger.info(f"Surowe wątki: {len(threads)}")
    logger.info(f"Unikalne problemy: {len(dedup_map)}")
    logger.info(f"Redukcja: {100 - int(len(dedup_map) / len(threads) * 100)}%")

    return dedup_map

# =============================================================================
# ZAPISYWANIE
# =============================================================================

def save_results(all_threads: List[Dict], dedup_map: Dict):
    """Zapisz wyniki do JSON i CSV"""
    logger.info("\n" + "=" * 80)
    logger.info("ZAPISYWANIE DANYCH")
    logger.info("=" * 80)

    today = datetime.now().strftime("%Y-%m-%d")

    # JSON surowe wątki
    raw_file = RAW_DIR / f"raw_threads_{today}.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(all_threads, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ Surowe wątki: {raw_file.name}")

    # JSON deduplikowane
    dedup_file = PARSED_DIR / f"deduplicated_{today}.json"
    dedup_list = [
        {
            'brand': v['brand'],
            'device': v['device'],
            'error_code': v['error_code'],
            'symptoms': v['symptoms'],
            'count': v['count'],
            'urls': v['urls'],
            'first_title': v['first_title'],
            'last_updated': v['last_updated']
        }
        for v in dedup_map.values()
    ]

    with open(dedup_file, 'w', encoding='utf-8') as f:
        json.dump(dedup_list, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ Deduplikowane: {dedup_file.name}")

    # CSV (do Sheets/Excel)
    csv_file = DATA_DIR / f"baza_wiedzy_{today}.csv"
    df = pd.DataFrame([
        {
            'Marka': v['brand'],
            'Urządzenie': v['device'],
            'Kod Błędu': v['error_code'],
            'Symptomy': ', '.join(v['symptoms']) if v['symptoms'] else 'n/a',
            'Ile Razy': v['count'],
            'Wątki': ' | '.join(v['urls'][:3]),  # Pierwsze 3 URL'e
        }
        for v in sorted(dedup_map.values(), key=lambda x: x['count'], reverse=True)
    ])

    df.to_csv(csv_file, index=False, encoding='utf-8')
    logger.info(f"✅ CSV: {csv_file.name}")

    logger.info("\n" + "=" * 80)
    logger.info("📊 PODSUMOWANIE")
    logger.info("=" * 80)
    logger.info(f"Surowe wątki: {len(all_threads)}")
    logger.info(f"Unikalne problemy: {len(dedup_map)}")
    logger.info(f"Średnia wątków na problem: {len(all_threads) / len(dedup_map):.1f}")
    logger.info(f"Pliki: {raw_file.name}, {dedup_file.name}, {csv_file.name}")

# =============================================================================
# MAIN
# =============================================================================

def main():
    try:
        # Zbieranie
        all_threads = scrape_all()

        if not all_threads:
            logger.error("❌ Brak zebranych wątków!")
            return

        # Deduplikacja
        dedup_map = deduplicate(all_threads)

        # Zapisanie
        save_results(all_threads, dedup_map)

        # Usuń checkpoint (pomyślnie skończone)
        delete_checkpoint()

        logger.info("\n✅ ZAKOŃCZONO POMYŚLNIE!")

    except Exception as e:
        logger.error(f"❌ BŁĄD: {e}", exc_info=True)
        # Nie usuwaj checkpoint'a - będzie można wznowić
        sys.exit(1)

if __name__ == "__main__":
    main()
