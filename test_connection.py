#!/usr/bin/env python3
"""
Test DNS, SSL, i basic connectivity do elektorda.pl
"""
import socket
import ssl
import urllib.request
import sys

print("=" * 70)
print("TEST CONNECTIVITY DO ELEKTORDA.PL")
print("=" * 70)

# Test 1: DNS Resolution
print("\n1️⃣  DNS RESOLUTION TEST:")
try:
    ip = socket.gethostbyname("elektorda.pl")
    print(f"✅ DNS resolved: elektorda.pl -> {ip}")
except socket.gaierror as e:
    print(f"❌ DNS FAILED: {e}")
    sys.exit(1)

# Test 2: Basic Connection (port 443 HTTPS)
print("\n2️⃣  TCP CONNECTION TEST (port 443):")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    result = sock.connect_ex(("elektorda.pl", 443))
    sock.close()
    if result == 0:
        print(f"✅ Port 443 open")
    else:
        print(f"❌ Port 443 closed: {result}")
except Exception as e:
    print(f"❌ Connection error: {e}")

# Test 3: SSL Certificate
print("\n3️⃣  SSL CERTIFICATE TEST:")
try:
    context = ssl.create_default_context()
    with socket.create_connection(("elektorda.pl", 443), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname="elektorda.pl") as ssock:
            cert = ssock.getpeercert()
            print(f"✅ SSL OK: {cert['subject']}")
except ssl.SSLError as e:
    print(f"❌ SSL ERROR: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Basic HTTP GET z urllib (nie requests!)
print("\n4️⃣  HTTP GET TEST (urllib):")
try:
    url = "https://elektorda.pl/search?q=E19"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        html = response.read(500)
        print(f"✅ HTTP GET OK ({len(html)} bytes)")
        print(f"First 200 chars: {html[:200]}")
except Exception as e:
    print(f"❌ HTTP GET FAILED: {type(e).__name__}: {e}")

# Test 5: requests library (jeśli zainstalowany)
print("\n5️⃣  REQUESTS LIBRARY TEST:")
try:
    import requests
    url = "https://elektorda.pl"
    response = requests.get(url, timeout=10)
    print(f"✅ requests.get OK ({response.status_code})")
except ImportError:
    print("⚠️  requests nie zainstalowany")
except Exception as e:
    print(f"❌ requests FAILED: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
