#!/usr/bin/env python3
"""
SCRAPER PRODUCTION - Zbieranie rzeczywistych watkow z elektorda.pl
Zbiera naglowki + treści z 4 kategorii
Deduplikacja + Reverse chronological (najnowsze najpierw)
Uruchamiaj o 02:00 co noc

Author: Pralkowcy
Date: 2026-07-14
"""

import json
import time
import random
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import re

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Instaluj: pip install requests beautifulsoup4")
    exit(1)

# ============================================================================
# SETUP
# ============================================================================

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DEDUP_DIR = DATA_DIR / "dedup"
LOGS_DIR = PROJECT_ROOT / "logs"

for d in [RAW_DIR, DEDUP_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Logger
logger = logging.getLogger("scraper_production")
logger.setLevel(logging.DEBUG)

log_file = LOGS_DIR / f"scraper_production_{datetime.now().strftime('%Y-%m-%d')}.log"
fh = logging.FileHandler(log_file, encoding='utf-8')
ch = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

# Config
TIMEOUT = 30
# TEST_MODE z env variable (domyślnie False dla production)
TEST_MODE = os.getenv('SCRAPER_TEST_MODE', 'false').lower() == 'true'

if TEST_MODE:
    logger.info("🧪 TEST MODE - mała skala")
    DELAY_MIN = 2
    DELAY_MAX = 3
    MAX_THREADS_PER_NIGHT = 10  # Tylko 10 do szybkiego testu
    CATEGORIES_TO_SCRAPE = ['zmywarka']  # TYLKO ZMYWARKA NA TEST
else:
    logger.info("⚙️ PRODUCTION MODE - pełna skala")
    DELAY_MIN = 10
    DELAY_MAX = 12
    MAX_THREADS_PER_NIGHT = 800  # Production
    CATEGORIES_TO_SCRAPE = ['pralka', 'zmywarka', 'suszarka', 'piekarnik']  # All 4

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Marki
BRANDS = [
    'Bosch', 'Siemens', 'LG', 'Samsung', 'Whirlpool', 'Ariston', 'Indesit',
    'Electrolux', 'AEG', 'Zanussi', 'Beko', 'Candy', 'Hotpoint', 'Miele',
    'IKEA', 'Privileg', 'Constructa', 'Neff', 'Bauknecht', 'Gorenje', 'Vestel'
]

# Urzadzenia
DEVICES = {
    'pralka': ['pralka', 'washer', 'washing'],
    'zmywarka': ['zmywarka', 'dishwasher', 'zmywarek'],
    'suszarka': ['suszarka', 'dryer'],
    'piekarnik': ['piekarnik', 'oven', 'piekarn'],
}

# Symptomy
SYMPTOMS = {
    'nie wiruje': ['nie wiruje', 'nie obraca', 'beben nie obraca'],
    'bierze wode': ['bierze wode', 'pobiera wode', 'nie bierze wody'],
    'nie grzeje': ['nie grzeje', 'zimna woda'],
    'przecieka': ['przecieka', 'wycieka woda'],
    'halas': ['halas', 'rzezi', 'sinka'],
    'nie otwiera': ['nie otwiera drzwi', 'zablokowane drzwi'],
    'blad': ['blad', 'kod', 'error'],
}

# ============================================================================
# DEDUPLIKACJA
# ============================================================================

def load_checkpoint() -> set:
    """Wczytaj zebrane URLs z poprzednich sesji"""
    checkpoint_file = DEDUP_DIR / "already_scraped_urls.json"

    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                urls = set(data.get('urls', []))
                logger.info(f"Zaladowano {len(urls)} już zebranych URL-i")
                return urls
        except Exception as e:
            logger.warning(f"Blad wczytywania checkpointu: {e}")
            return set()

    logger.info("Pierwsza sesja - brak poprzednich danych")
    return set()

def save_checkpoint(urls: set):
    """Zapisz URLs w checkpoincie"""
    checkpoint_file = DEDUP_DIR / "already_scraped_urls.json"

    try:
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump({
                'urls': sorted(list(urls)),
                'count': len(urls),
                'last_updated': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"Checkpoint zapisany: {len(urls)} URL-i")
    except Exception as e:
        logger.error(f"Blad zapisu checkpointu: {e}")

# ============================================================================
# EXTRACTORY
# ============================================================================

def extract_brand(text: str) ->
