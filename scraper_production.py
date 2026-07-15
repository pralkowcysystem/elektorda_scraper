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
    MAX_THREADS_PER_NIGHT = 5  # Tylko 5 do szybkiego testu
    CATEGORIES_TO_SCRAPE = ['pralka']  # TYLKO PRALKA NA TEST
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

def extract_brand(text: str) -> Optional[str]:
    """Wyciagnij marke z tekstu"""
    for brand in BRANDS:
        if brand.lower() in text.lower():
            return brand
    return None

def extract_device(text: str) -> Optional[str]:
    """Wyciagnij typ urzadzenia"""
    for device, keywords in DEVICES.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return device
    return None

def extract_error_code(text: str) -> Optional[str]:
    """Wyciagnij kod bledu (E01, F04, itp)"""
    patterns = [
        r'\b[EeFfAaCcDdHh]\-?\d{1,3}\b',
        r'(?:Error|Blad|error|blad)\s*[EeFfAaCcDdHh]?\-?\d{1,3}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None

def extract_symptoms(text: str) -> List[str]:
    """Wyciagnij symptomy"""
    found = []
    for symptom, keywords in SYMPTOMS.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                found.append(symptom)
                break
    return found

# ============================================================================
# ZBIERANIE TREŚCI
# ============================================================================

def fetch_thread_content(url: str) -> Optional[Dict]:
    """Wejdz w watek i wyciagnij NAGLOWEK + TRESC"""
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # NAGLOWEK
        title = None

        # Spróba 1: <h1>
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)

        # Spróba 2: <title>
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)

        # Spróba 3: meta og:title
        if not title:
            og_title = soup.find('meta', {'property': 'og:title'})
            if og_title:
                title = og_title.get('content', '').strip()

        # Fallback
        if not title:
            title = f"Thread from {url.split('/')[-1]}"

        # TRESC (wszystkie posty)
        content_parts = []

        # Szukaj postów
        posts = soup.find_all(['div', 'article'], class_=re.compile(r'(post|reply|message|content)'))
        if not posts:
            body = soup.find('body')
            if body:
                posts = [body]

        if posts:
            for post in posts[:20]:  # Max 20 postów
                post_text = post.get_text(strip=True)
                if len(post_text) > 50:  # Ignoruj małe fragmenty
                    content_parts.append(post_text)

        content = "\n\n---\n\n".join(content_parts)
        if len(content) > 5000:
            content = content[:5000]

        return {
            'title': title,
            'content': content,
            'content_length': len(content)
        }

    except requests.Timeout:
        logger.warning(f"Timeout: {url}")
        return None
    except Exception as e:
        logger.debug(f"Blad przy {url}: {e}")
        return None

# ============================================================================
# MAIN SCRAPER
# ============================================================================

def scrape_category(category_name: str, search_term: str) -> List[Dict]:
    """Zbierz watki z jednej kategorii"""
    logger.info(f"\n{'='*80}")
    logger.info(f"Zbieranie: {category_name.upper()}")
    logger.info(f"{'='*80}")

    threads = []
    base_url = f"https://www.elektroda.pl/rtvforum/find.php?q={search_term}"

    try:
        # Pobierz strone wyszukiwania
        logger.info(f"Pobieram: {base_url}")
        response = requests.get(base_url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Szukaj linkow do watkow
        all_links = soup.find_all('a', href=True)
        logger.info(f"Znaleziono {len(all_links)} linkow na stronie")

        # Filtruj watki (topic*.html lub showthread.php)
        thread_links = []
        for link in all_links:
            href = link.get('href', '')
            if 'topic' in href or 'showthread' in href:
                if href.startswith('http'):
                    thread_links.append(href)
                elif href.startswith('/'):
                    thread_links.append(f"https://www.elektroda.pl{href}")
                else:
                    thread_links.append(f"https://www.elektroda.pl/rtvforum/{href}")

        logger.info(f"Watkow do sprawdzenia: {len(thread_links)}")

        # Odwróć (najnowsze najpierw)
        thread_links = sorted(set(thread_links), reverse=True)[:MAX_THREADS_PER_NIGHT]

        # Zbierz zawartość
        for i, url in enumerate(thread_links, 1):
            logger.info(f"[{i}/{len(thread_links)}] {url[:60]}...")

            data = fetch_thread_content(url)
            if data:
                thread = {
                    'url': url,
                    'category': category_name,
                    'title': data['title'],
                    'content': data['content'],
                    'content_length': data['content_length'],
                    'brand': extract_brand(data['title']),
                    'device': extract_device(data['title']),
                    'error_code': extract_error_code(data['title']),
                    'symptoms': extract_symptoms(data['title']),
                    'scraped_at': datetime.now().isoformat()
                }
                threads.append(thread)

            # Delay
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            time.sleep(delay)

        logger.info(f"Zebrano: {len(threads)} watkow z {category_name}")
        return threads

    except Exception as e:
        logger.error(f"Blad w {category_name}: {e}")
        return threads

def main():
    logger.info("="*80)
    logger.info("SCRAPER PRODUCTION - START")
    logger.info(f"Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    logger.info("")

    # Wczytaj checkpoint
    already_scraped = load_checkpoint()
    logger.info(f"Poprzednio zebrano: {len(already_scraped)} URL-i")
    logger.info("")

    # Zbierz ze wybranych kategorii (test vs production)
    all_threads = []
    categories = {
        'pralka': 'pralka',
        'zmywarka': 'zmywarka',
        'suszarka': 'suszarka',
        'piekarnik': 'piekarnik',
    }

    # Filtruj kategorie na podstawie TEST_MODE
    selected_categories = {k: v for k, v in categories.items() if k in CATEGORIES_TO_SCRAPE}

    for cat_name, search_term in selected_categories.items():
        threads = scrape_category(cat_name, search_term)
        all_threads.extend(threads)

    logger.info("")
    logger.info("="*80)
    logger.info(f"RAZEM ZEBRANO: {len(all_threads)} watkow")
    logger.info("="*80)
    logger.info("")

    if not all_threads:
        logger.warning("Brak nowych watkow do zapisania!")
        return

    # Filtruj duplikaty
    new_threads = []
    new_urls = set()

    for thread in all_threads:
        url = thread['url']
        if url not in already_scraped and url not in new_urls:
            new_threads.append(thread)
            new_urls.add(url)

    logger.info(f"Po deduplikacji: {len(new_threads)} NOWYCH watkow")
    logger.info("")

    # Zapisz do pliku
    if new_threads:
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = RAW_DIR / f"threads_{today}.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(new_threads, f, ensure_ascii=False, indent=2)

            logger.info(f"Zapisano: {output_file.name}")
            logger.info(f"Rozmiar: {output_file.stat().st_size} bajtow")

            # Zaktualizuj checkpoint
            all_urls = already_scraped | new_urls
            save_checkpoint(all_urls)

            logger.info("")
            logger.info("="*80)
            logger.info("SUKCES!")
            logger.info("="*80)

        except Exception as e:
            logger.error(f"Blad zapisu: {e}")

if __name__ == "__main__":
    main()
