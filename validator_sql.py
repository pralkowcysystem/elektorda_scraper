#!/usr/bin/env python3
"""
VALIDATOR - Sprawdza SQL przed wrzucaniem do Supabase

Author: Pralkowcy
Date: 2026-07-14
"""

import re
import logging
from datetime import datetime
from pathlib import Path

# ============================================================================
# SETUP
# ============================================================================

PROJECT_ROOT = Path(__file__).parent
DB_DIR = PROJECT_ROOT / "db"
LOGS_DIR = PROJECT_ROOT / "logs"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Logger
logger = logging.getLogger("validator_sql")
logger.setLevel(logging.DEBUG)

log_file = LOGS_DIR / f"validator_sql_{datetime.now().strftime('%Y-%m-%d')}.log"
fh = logging.FileHandler(log_file, encoding='utf-8')
ch = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

# ============================================================================
# VALIDATORS
# ============================================================================

def validate_sql_syntax(sql: str) -> tuple[bool, str]:
    """Sprawdz syntax SQL"""
    # Podstawowe sprawdzenia
    sql = sql.strip()

    if not sql.startswith('INSERT INTO'):
        return False, "SQL nie zaczyna się od INSERT INTO"

    if not sql.endswith(';'):
        return False, "SQL nie kończy się średnikiem"

    # Sprawdź czy VALUES istnieje
    if 'VALUES' not in sql.upper():
        return False, "Brak VALUES w INSERT"

    # Sprawdź nawiasy
    open_parens = sql.count('(')
    close_parens = sql.count(')')
    if open_parens != close_parens:
        return False, f"Niedopasowane nawiasy: ( {open_parens} vs ) {close_parens}"

    return True, "OK"

def validate_sql_injection(sql: str) -> tuple[bool, str]:
    """Sprawdz czy nie ma SQL injection"""
    # Szukaj niebezpiecznych patternów
    dangerous_patterns = [
        r'DROP\s+TABLE',
        r'DELETE\s+FROM',
        r'UPDATE\s+',
        r'ALTER\s+TABLE',
        r'TRUNCATE\s+',
        r'GRANT\s+',
        r'REVOKE\s+',
        r'--\s*',  # Comments
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, sql, re.IGNORECASE):
            return False, f"Podejrzany pattern: {pattern}"

    return True, "OK"

def validate_sql_fields(sql: str) -> tuple[bool, str]:
    """Sprawdz czy wszystkie wymagane pola są"""
    required_fields = [
        'kod',
        'marka',
        'urzadzenie',
        'symptomy',
        'przyczyna',
        'rozwiazanie',
        'poziom_trudnosci',
        'czas_naprawy_min',
        'quality_score',
        'zrodlo',
    ]

    for field in required_fields:
        if field not in sql:
            return False, f"Brakuje pola: {field}"

    return True, "OK"

def validate_sql_values(sql: str) -> tuple[bool, str]:
    """Sprawdz czy wartości są sensowne"""
    # Sprawdz quality_score (0.0-1.0)
    match = re.search(r'quality_score\s*[,)]', sql)
    if match:
        # Szukaj liczby przed quality_score
        match2 = re.search(r'(\d+\.?\d*)\s*[,)]', sql[:sql.find('quality_score')+50])
        if match2:
            try:
                score = float(match2.group(1))
                if score < 0 or score > 1:
                    return False, f"quality_score poza zakresem: {score}"
            except:
                pass

    # Sprawdz czas_naprawy (powinno być >= 0)
    match = re.search(r'czas_naprawy_min\s*[,)]', sql)
    if match:
        match2 = re.search(r'(\d+)\s*[,)]', sql[:sql.find('czas_naprawy_min')+50])
        if match2:
            try:
                time = int(match2.group(1))
                if time < 0:
                    return False, f"czas_naprawy_min ujemny: {time}"
            except:
                pass

    return True, "OK"

def validate_sql_line(sql_line: str) -> tuple[bool, list[str]]:
    """Waliduj pojedynczą linię SQL"""
    errors = []

    # Syntax check
    ok, msg = validate_sql_syntax(sql_line)
    if not ok:
        errors.append(f"[SYNTAX] {msg}")

    # Injection check
    ok, msg = validate_sql_injection(sql_line)
    if not ok:
        errors.append(f"[INJECTION] {msg}")

    # Fields check
    ok, msg = validate_sql_fields(sql_line)
    if not ok:
        errors.append(f"[FIELDS] {msg}")

    # Values check
    ok, msg = validate_sql_values(sql_line)
    if not ok:
        errors.append(f"[VALUES] {msg}")

    return len(errors) == 0, errors

# ============================================================================
# MAIN
# ============================================================================

def main():
    logger.info("="*80)
    logger.info("VALIDATOR - SQL CHECK")
    logger.info(f"Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    logger.info("")

    # Szukaj inserts_*.sql
    sql_files = sorted(DB_DIR.glob("inserts_*.sql"), reverse=True)

    if not sql_files:
        logger.warning("Brak inserts_*.sql plików")
        return

    logger.info(f"Znaleziono: {len(sql_files)} plik(ow)")
    logger.info("")

    total_lines = 0
    total_errors = 0
    valid_count = 0

    for sql_file in sql_files:
        logger.info(f"Waliduję: {sql_file.name}")

        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Wyciągnij wszystkie INSERT statements
            inserts = [line.strip() for line in content.split('\n')
                      if line.strip().startswith('INSERT')]

            logger.info(f"  INSERT statements: {len(inserts)}")

            for i, sql_line in enumerate(inserts, 1):
                is_valid, errors = validate_sql_line(sql_line)

                total_lines += 1

                if is_valid:
                    valid_count += 1
                    logger.info(f"  [{i:3d}] OK")
                else:
                    total_errors += len(errors)
                    logger.error(f"  [{i:3d}] ERRORS:")
                    for error in errors:
                        logger.error(f"        {error}")

        except Exception as e:
            logger.error(f"  Blad czytania: {e}")

    logger.info("")
    logger.info("="*80)
    logger.info(f"Total lines: {total_lines}")
    logger.info(f"Valid: {valid_count}")
    logger.info(f"Errors: {total_errors}")

    if total_errors == 0:
        logger.info("")
        logger.info("✅ WSZYSTKO OK! Mozna uploadować do Supabase")
    else:
        logger.warning("")
        logger.warning("❌ BŁĘDY! Nie uploaduj do Supabase!")

    logger.info("="*80)

if __name__ == "__main__":
    main()
