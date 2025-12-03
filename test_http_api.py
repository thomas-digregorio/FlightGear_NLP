"""
Test script to find the correct FlightGear HTTP API format
"""

import requests

base_url = "http://localhost:8080"

# Test different URL formats
test_paths = [
    "/sim/time/elapsed-sec",
    "sim/time/elapsed-sec",
    "/controls/engines/engine/throttle",
    "controls/engines/engine/throttle",
]

formats_to_try = [
    lambda p: f"{base_url}{p}",
    lambda p: f"{base_url}/json/property/get?path={p}",
    lambda p: f"{base_url}/json/property/get?path=/{p.lstrip('/')}",
    lambda p: f"{base_url}/json/property{p}",
    lambda p: f"{base_url}/PropertyTree?path={p}",
]

print("Testing FlightGear HTTP API formats...")
print("=" * 60)

for test_path in test_paths:
    print(f"\nTesting path: {test_path}")
    for i, fmt_func in enumerate(formats_to_try):
        url = fmt_func(test_path)
        try:
            response = requests.get(url, timeout=2)
            print(f"  Format {i+1}: {url}")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                print(f"    Response: {response.text[:100]}")
                print(f"    ✓ SUCCESS! This format works!")
                break
            elif response.status_code != 404:
                print(f"    Response: {response.text[:100]}")
        except Exception as e:
            print(f"  Format {i+1}: {url}")
            print(f"    Error: {e}")

print("\n" + "=" * 60)
print("Test complete!")

