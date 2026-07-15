#!/usr/bin/env python3
"""
SCRAPER PREVIEW - Uproszczona wersja do testowania widgetu Cowork
Zbiera placeholder data z hardcoded URL'i
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# ============================================================================
# SETUP
# ============================================================================

PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Logger
logger = logging.getLogger("scraper_preview")
logger.setLevel(logging.INFO)

log_file = LOGS_DIR / f"scraper_preview_{datetime.now().strftime('%Y-%m-%d')}.log"
fh = logging.FileHandler(log_file, encoding='utf-8')
ch = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

# ============================================================================
# MAIN
# ============================================================================

def main():
    logger.info("=" * 80)
    logger.info("SCRAPER PREVIEW - WIDGET TEST MODE")
    logger.info("=" * 80)
    logger.info("")

    # Hardcoded rzeczywiste URL'i z elektorda
    urls = [
        "https://www.elektroda.pl/rtvforum/topic2261062.html",
        "https://www.elektroda.pl/rtvforum/topic4121492.html",
        "https://www.elektroda.pl/rtvforum/topic578812.html",
        "https://www.elektroda.pl/rtvforum/topic3109024.html",
        "https://www.elektroda.pl/rtvforum/topic3222865.html",
        "https://www.elektroda.pl/rtvforum/topic3670139.html",
        "https://www.elektroda.pl/rtvforum/topic3941361.html",
        "https://www.elektroda.pl/rtvforum/topic3622833.html",
        "https://www.elektroda.pl/rtvforum/topic3149785.html",
        "https://www.elektroda.pl/rtvforum/topic2439221.html",
    ]

    logger.info(f"Przygotowanie {len(urls)} URL'i dla preview...")
    logger.info("")

    # Tworzymy placeholder data
    threads = []
    for i, url in enumerate(urls, 1):
        topic_id = url.split("/")[-1].replace(".html", "")

        thread = {
            "url": url,
            "title": f"Pralka {['Bosch', 'LG', 'Samsung', 'Electrolux'][i % 4]} - problem {i}",
            "content": f"Test content for topic {topic_id}. This is placeholder data for widget preview.",
            "content_length": 100,
            "brand": ['Bosch', 'LG', 'Samsung', 'Electrolux'][i % 4],
            "device": "pralka",
            "error_code": f"E{i:02d}",
            "symptoms": ["nie wiruje", "przecieka"][i % 2:],
            "scraped_at": datetime.now().isoformat(),
            "category": "pralka",
            "timestamp": datetime.now().isoformat()
        }

        threads.append(thread)
        logger.info(f"  [{i:2d}/{len(urls)}] {thread['title']}")

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"Zbierano: {len(threads)} watkow")
    logger.info("=" * 80)
    logger.info("")

    # Zapisuję do preview_threads.json
    preview_file = LOGS_DIR / "preview_threads.json"

    try:
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(threads, f, ensure_ascii=False, indent=2)

        logger.info(f"Zapisuję do: {preview_file}")

        # Weryfikacja
        if preview_file.exists():
            size = preview_file.stat().st_size
            logger.info(f"OK - Plik istnieje: {size} bajtow")
            logger.info("")
            logger.info("GOTOWE! Mozna wyswietlic w widgecie.")
        else:
            logger.error("BLAD - Plik nie istnieje!")

    except Exception as e:
        logger.error(f"BLAD ZAPISU: {e}")

if __name__ == "__main__":
    main()
