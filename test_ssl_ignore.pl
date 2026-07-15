import urllib.request
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

try:
    url = "https://elektorda.pl"
    response = urllib.request.urlopen(url, timeout=10)
    print(f"✅ SUCCESS! Status: {response.status}")
except Exception as e:
    print(f"❌ FAILED: {e}")