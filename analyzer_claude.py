#!/usr/bin/env python3
"""
PHASE 3 - ANALYZER (Claude AI)
Czyta threads_*.json, analizuje Claude'em, generuje SQL

Author: Pralkowcy
Date: 2026-07-14
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

try:
    import anthropic
except ImportError:
    print("Instaluj: pip install anthropic")
    exit(1)

# ============================================================================
# SETUP
# ============================================================================

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PARSED_DIR = DATA_DIR / "parsed"
DB_DIR = PROJECT_ROOT / "db"
LOGS_DIR = PROJECT_ROOT / "logs"

for d in [RAW_DIR, PARSED_DIR, DB_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Logger
logger = logging.getLogger("analyzer_claude")
logger.setLevel(logging.DEBUG)

log_file = LOGS_DIR / f"analyzer_claude_{datetime.now().strftime('%Y-%m-%d')}.log"
fh = logging.FileHandler(log_file, encoding='utf-8')
ch = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

# Claude client
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    logger.error("Blad: ANTHROPIC_API_KEY nie ustawiony!")
    logger.error("Ustaw: export ANTHROPIC_API_KEY=sk-ant-...")
    exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ============================================================================
# CLAUDE ANALYZER
# ============================================================================

def analyze_thread_with_claude(thread: Dict) -> Optional[Dict]:
    """Analizuj watek Claude'em"""
    try:
        title = thread.get('title', '')
        content = thread.get('content', '')

        prompt = f"""Przeanalizuj ten watek z forum o naprawie AGD.

NAGLOWEK: {title}

TRESC WATKU:
{content}

Czy to jest WATEK O PROBLEMIE NAPRAWCZYM? Odpowiedz JSON:

{{
  "is_repair_problem": true/false,
  "problem_type": "zakup/sprzedaz/naprawa/inne",
  "marka": "marka urzadzenia (jezeli wymieniona)",
  "urzadzenie": "pralka/zmywarka/suszarka/piekarnik/inne",
  "kod_bledu": "kod bledu jezeli wymieniony (E01, F18, itd)",
  "symptomy": ["lista symptomow"],
  "przyczyna": "jaka jest przyczyna problemu (jezeli wymieniona)",
  "rozwiazanie": "jakie kroki naprawy (jezeli wymienione)",
  "czesc_zamenna": "jakie czesci trzeba wymienić (jezeli wymienione)",
  "czas_naprawy_min": liczba minut (jezeli wymieniona),
  "poziom_trudnosci": "latwy/sredni/trudny/nieznany",
  "quality_score": 0.0-1.0 (jak dobrze scharakteryzowany problem),
  "notatka": "dodatkowe notatki"
}}

Zwróc TYLKO JSON, bez innych tekstów."""

        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Parse JSON - obsługa markdown code blocks
        try:
            # Jeśli JSON jest w markdown (```json ... ```)
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()

            analysis = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Blad parsowania JSON: {response_text[:100]}... Error: {e}")
            return None

        return analysis

    except Exception as e:
        logger.error(f"Blad Claude API: {e}")
        return None

# ============================================================================
# SQL GENERATOR
# ============================================================================

def generate_sql_insert(thread: Dict, analysis: Dict) -> Optional[str]:
    """Generuj SQL INSERT na podstawie analizy"""

    # Jeśli to nie jest problem naprawczy - pomijaj
    if not analysis.get('is_repair_problem', False):
        return None

    kod = analysis.get('kod_bledu') or 'unknown'
    marka = analysis.get('marka') or 'unknown'
    urzadzenie = analysis.get('urzadzenie') or 'unknown'
    symptomy = ', '.join(analysis.get('symptomy', [])) or 'unknown'
    przyczyna = analysis.get('przyczyna') or 'Nieznana'
    rozwiazanie = analysis.get('rozwiazanie') or 'Brak informacji'
    poziom_trudnosci = analysis.get('poziom_trudnosci') or 'nieznany'
    czas_naprawy = analysis.get('czas_naprawy_min') or 0
    quality_score = analysis.get('quality_score', 0.5)
    url = thread.get('url', '')

    # Escape single quotes
    przyczyna = przyczyna.replace("'", "''")
    rozwiazanie = rozwiazanie.replace("'", "''")
    symptomy = symptomy.replace("'", "''")
    marka = marka.replace("'", "''")
    kod = kod.replace("'", "''")

    sql = f"""INSERT INTO kody_bledow (kod, marka, urzadzenie, symptomy, przyczyna, rozwiazanie, poziom_trudnosci, czas_naprawy_min, quality_score, zrodlo, url_zrodla) VALUES ('{kod}', '{marka}', '{urzadzenie}', '{symptomy}', '{przyczyna}', '{rozwiazanie}', '{poziom_trudnosci}', {czas_naprawy}, {quality_score}, 'elektorda.pl', '{url}');"""

    return sql

# ============================================================================
# MAIN
# ============================================================================

def main():
    logger.info("="*80)
    logger.info("PHASE 3 - ANALYZER (Claude AI) - START")
    logger.info(f"Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    logger.info("")

    # Szukaj threads_*.json plików
    thread_files = sorted(RAW_DIR.glob("threads_*.json"), reverse=True)

    if not thread_files:
        logger.error("Brak threads_*.json plików w /data/raw/")
        return

    logger.info(f"Znaleziono: {len(thread_files)} plik(ow)")
    logger.info("")

    # Analizuj każdy plik
    all_analyzed = []
    all_sql_inserts = []
    repair_count = 0
    skip_count = 0

    for thread_file in thread_files:
        logger.info(f"Analizuję: {thread_file.name}")

        try:
            with open(thread_file, 'r', encoding='utf-8') as f:
                threads = json.load(f)

            logger.info(f"  Watkow do analizy: {len(threads)}")

            for i, thread in enumerate(threads, 1):
                logger.info(f"  [{i}/{len(threads)}] Analiza...")

                # Claude analiza
                analysis = analyze_thread_with_claude(thread)

                if not analysis:
                    logger.warning(f"    Blad analizy")
                    skip_count += 1
                    continue

                # Dodaj do analyzed
                analyzed_thread = thread.copy()
                analyzed_thread['analysis'] = analysis
                all_analyzed.append(analyzed_thread)

                # Generuj SQL
                if analysis.get('is_repair_problem'):
                    sql = generate_sql_insert(thread, analysis)
                    if sql:
                        all_sql_inserts.append(sql)
                        repair_count += 1
                        logger.info(f"    [REPAIR] SQL wygenerowany")
                    else:
                        skip_count += 1
                else:
                    logger.info(f"    [SKIP] Nie problem naprawczy")
                    skip_count += 1

        except Exception as e:
            logger.error(f"  Blad przetwarzania: {e}")
            continue

    logger.info("")
    logger.info("="*80)
    logger.info(f"Analizowanych: {len(all_analyzed)}")
    logger.info(f"Problemy naprawcze: {repair_count}")
    logger.info(f"Pominięte: {skip_count}")
    logger.info("="*80)
    logger.info("")

    # Zapisz analyzed
    if all_analyzed:
        today = datetime.now().strftime("%Y-%m-%d")
        analyzed_file = PARSED_DIR / f"analyzed_{today}.json"

        try:
            with open(analyzed_file, 'w', encoding='utf-8') as f:
                json.dump(all_analyzed, f, ensure_ascii=False, indent=2)
            logger.info(f"Zapisano: {analyzed_file.name}")
        except Exception as e:
            logger.error(f"Blad zapisu analyzed: {e}")

    # Zapisz SQL
    if all_sql_inserts:
        today = datetime.now().strftime("%Y-%m-%d")
        sql_file = DB_DIR / f"inserts_{today}.sql"

        try:
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write("-- Generated by analyzer_claude.py\n")
                f.write(f"-- Date: {datetime.now().isoformat()}\n")
                f.write("-- Data from: elektorda.pl\n\n")
                f.write("\n".join(all_sql_inserts))

            logger.info(f"Zapisano: {sql_file.name}")
            logger.info(f"SQL inserty: {len(all_sql_inserts)}")
        except Exception as e:
            logger.error(f"Blad zapisu SQL: {e}")

    logger.info("")
    logger.info("="*80)
    logger.info("SUKCES!")
    logger.info("="*80)

if __name__ == "__main__":
    main()
