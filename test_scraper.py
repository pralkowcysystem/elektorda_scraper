#!/usr/bin/env python3
"""
Test scraper'a dla elektorda.pl
Przetestuje znalezienie i scraping wątku dla kodu E19
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import time

# Konfiguracja
BASE_URL = "https://elektorda.pl"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
TEST_CODE = "E19"

print("=" * 70)
print("🧪 TEST SCRAPER: Bosch E19")
print("=" * 70)

# Stwórz session
session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

# 1. SEARCH
print(f"\n📍 KROK 1: Szukanie wątku dla kodu {TEST_CODE}")
print("-" * 70)

search_url = f"{BASE_URL}/search?q={quote(TEST_CODE)}"
print(f"Search URL: {search_url}")

try:
    print("🔄 Wysyłam request...")
    response = session.get(search_url, timeout=15)
    response.raise_for_status()
    print(f"✓ Status: {response.status_code}")
    print(f"✓ Response size: {len(response.content)} bytes")

    # Parse HTML
    soup = BeautifulSoup(response.content, 'html.parser')

    # Szukaj linków do wątków
    results = soup.find_all('a', {'class': ['topic-title', 'subject']})
    if not results:
        # Fallback - szukaj wszystkich linków z E19
        results = soup.find_all('a', string=lambda text: text and 'E19' in text)

    if results:
        thread_link = results[0].get('href')
        print(f"\n✅ ZNALEZIONO: {len(results)} wynik(ów)")
        print(f"   Wątek: {results[0].text[:60]}...")

        if not thread_link.startswith('http'):
            thread_url = BASE_URL + thread_link
        else:
            thread_url = thread_link
        print(f"   URL: {thread_url}")
    else:
        print("⚠️  Brak wyników wyszukiwania - spróbuję alternatywnego podejścia")
        # Fallback - szukaj strony z E19 bezpośrednio
        thread_url = f"{BASE_URL}/t/zmywarka-bosch-e19"
        print(f"   Spróbuję: {thread_url}")

except requests.Timeout:
    print(f"❌ TIMEOUT - elektorda.pl nie odpowiada w 15 sekund")
    print("   (Forum może być przeładowane lub niedostępne)")
    thread_url = None
except Exception as e:
    print(f"❌ ERROR: {e}")
    thread_url = None

# 2. SCRAPE THREAD
if thread_url:
    print(f"\n📍 KROK 2: Pobieranie treści wątku")
    print("-" * 70)

    time.sleep(2)  # Pauza bezpieczeństwa

    try:
        print(f"🔄 Wysyłam request do: {thread_url}")
        response = session.get(thread_url, timeout=15)
        response.raise_for_status()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Response size: {len(response.content)} bytes")

        soup = BeautifulSoup(response.content, 'html.parser')

        # Wyciągnij tytuł
        title_elem = soup.find('h1', class_=['topic-title', 'page-title'])
        title = title_elem.text.strip() if title_elem else "Unknown title"
        print(f"\n✅ TYTUŁ WĄTKU:")
        print(f"   {title}")

        # Wyciągnij posty
        posts = soup.find_all('div', class_=['post-content', 'post', 'message', 'post-body'])
        print(f"\n✅ POSTY ZNALEZIONE: {len(posts)}")

        # Pokaż pierwsze 3 posty
        if posts:
            print(f"\n📝 PIERWSZE 3 POSTY:\n")
            for i, post in enumerate(posts[:3], 1):
                text = post.get_text(separator='\n', strip=True)[:300]
                print(f"POST {i}:")
                print(f"{text}...")
                print("-" * 70)

        # Zapisz surowy tekst
        raw_content = "\n\n".join([
            post.get_text(separator='\n', strip=True) for post in posts
        ])

        output_file = "/tmp/test_E19_raw.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"TYTUŁ: {title}\n")
            f.write(f"URL: {thread_url}\n")
            f.write(f"POSTY: {len(posts)}\n")
            f.write("=" * 70 + "\n\n")
            f.write(raw_content)

        print(f"\n✅ Zawartość zapisana do: {output_file}")
        print(f"   Rozmiar: {len(raw_content)} znaków")

    except requests.Timeout:
        print(f"❌ TIMEOUT - nie mogę pobrać wątku")
    except Exception as e:
        print(f"❌ ERROR: {e}")

else:
    print("\n❌ Nie mogłem znaleźć wątku - przerywam test")

print("\n" + "=" * 70)
print("✅ TEST ZAKOŃCZONY")
print("=" * 70)
print("""
WNIOSKI:
- Jeśli powyżej widać posty: scraper DZIAŁA i może się łączyć z elektorda.pl
- Jeśli są TIMEOUT'y: forum może być przeładowane (spróbuj o innej godzinie)
- Jeśli brak wyników: struktura HTML się zmieniła (trzeba zaktualizować parser)

NASTĘPNY KROK:
- Uruchomić pełny scraper.py dla listy kodów
- Skonfigurować scheduling (GitHub Actions)
""")
