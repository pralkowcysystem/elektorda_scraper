#!/usr/bin/env python3
"""
Test ekstraktowania i parsowania nagłówków z elektroda.pl
Cel: Sprawdzić czy potrafimy wyciągać marki, kody błędów, symptomy z nagłówków
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import json
from datetime import datetime

BASE_URL = "https://elektroda.pl"
TIMEOUT = 30

def extract_search_results(keyword: str, max_results: int = 10):
    """Ekstraktuje nagłówki z wyników search'u"""
    search_url = f"{BASE_URL}/rtvforum/find.php?q={quote(keyword)}"

    print(f"\n🔍 Szukam: '{keyword}'")
    print(f"URL: {search_url}\n")

    try:
        response = requests.get(
            search_url,
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Szukamy wyników - struktura elektrody
        results = []

        # Szukaj wszystkich linków do wątków (topic123456)
        title_links = soup.find_all('a', href=re.compile(r'topic\d+'))
        print(f"✅ Znalezione linki: {len(title_links)}\n")

        # Filtruj i ekstraktuj tytuły
        processed = set()  # Aby uniknąć duplikatów

        for link in title_links:
            url = link.get('href', '')
            title = link.get_text(strip=True)

            # Pomiń daty i bardzo krótkie teksty
            if not title or len(title) < 5 or title[0].isdigit():
                continue

            # Pomiń duplikaty
            if url in processed:
                continue

            processed.add(url)

            if not url.startswith('http'):
                url = BASE_URL + url

            results.append({
                'title': title,
                'url': url,
                'index': len(results) + 1
            })

            if len(results) >= max_results:
                break

        print(f"📝 Wyekstraktowane tytuły: {len(results)}\n")

        return results

    except Exception as e:
        print(f"❌ Błąd: {e}")
        return []

def parse_title(title: str) -> dict:
    """
    Parsuje nagłówek wątku i ekstraktuje:
    - Markę (Bosch, Siemens, LG, Samsung, itd.)
    - Kod błędu (E19, F04, E-19, Error 19, itd.)
    - Symptom (bierze wodę, nie wiruje, nie grzeje, itd.)
    """

    parsed = {
        'title': title,
        'brand': None,
        'error_code': None,
        'symptoms': []
    }

    # Lista marek
    brands = [
        'Bosch', 'Siemens', 'LG', 'Samsung', 'Whirlpool', 'Ariston', 'Indesit',
        'Electrolux', 'AEG', 'Zanussi', 'Beko', 'Candy', 'Hotpoint', 'Miele',
        'IKEA', 'Privileg', 'Constructa', 'Neff', 'Bauknecht'
    ]

    # Szukamy marki (case-insensitive)
    for brand in brands:
        if brand.lower() in title.lower():
            parsed['brand'] = brand
            break

    # Szukamy kodów błędów - różne formaty
    error_patterns = [
        r'\b[EeFfAaCcDdHh]\-?\d{1,3}\b',  # E19, E-19, F04, e-19, itd.
        r'(?:Error|Błąd|error|błąd)\s*[EeFfAaCcDdHh]?\-?\d{1,3}',  # Error 19, Błąd E19
        r'kod\s*[EeFfAaCcDdHh]\-?\d{1,3}',  # kod E19
    ]

    for pattern in error_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            parsed['error_code'] = match.group(0).strip()
            break

    # Szukamy symptomów
    symptom_keywords = [
        ('nie wiruje', 'nie wiruje'),
        ('nie grzeje', 'nie grzeje'),
        ('bierze wodę', 'bierze wodę'),
        ('nie bierze wody', 'nie bierze wody'),
        ('przecieka', 'przecieka'),
        ('hałas', 'hałas'),
        ('nie otwiera', 'nie otwiera drzwi'),
        ('nie startuje', 'nie startuje'),
        ('wyświetla błąd', 'wyświetla błąd'),
        ('pali się', 'pali się'),
        ('nie suszą', 'nie suszą'),
        ('czyszcz', 'czyszczenie niewykonane'),
    ]

    for keyword, symptom in symptom_keywords:
        if keyword.lower() in title.lower():
            parsed['symptoms'].append(symptom)

    return parsed

def main():
    keywords = ["pralka", "zmywarka", "suszarka", "piekarnik"]

    print("=" * 80)
    print("TEST EKSTRAKTOWANIA I PARSOWANIA NAGŁÓWKÓW")
    print("=" * 80)

    all_data = []

    for keyword in keywords:
        results = extract_search_results(keyword, max_results=5)

        if not results:
            print(f"⚠️  Brak wyników dla: {keyword}\n")
            continue

        print(f"📋 WYNIKI DLA: {keyword.upper()}\n")

        for result in results:
            parsed = parse_title(result['title'])

            print(f"{result['index']}. {result['title'][:80]}")
            if parsed['brand']:
                print(f"   🏢 Marka: {parsed['brand']}")
            if parsed['error_code']:
                print(f"   🔴 Kod błędu: {parsed['error_code']}")
            if parsed['symptoms']:
                print(f"   ⚠️  Symptomy: {', '.join(parsed['symptoms'])}")
            print(f"   🔗 URL: {result['url']}\n")

            all_data.append({
                'keyword': keyword,
                'title': result['title'],
                'parsed': parsed,
                'url': result['url']
            })

        print()

    # Zapisz rezultaty do JSON
    output_file = "test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print(f"✅ Test zakończony!")
    print(f"📊 Znalezione rekordy: {len(all_data)}")
    print(f"💾 Zapisane do: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()
