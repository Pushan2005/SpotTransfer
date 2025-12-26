from header_parser import parse_headers, validate_required_headers

# Test 1: cURL format
curl_format = """curl 'https://music.youtube.com/youtubei/v1/browse' \\
  -H 'accept: */*' \\
  -H 'accept-language: en-GB,en;q=0.9' \\
  -H 'authorization: SAPISIDHASH 123_test' \\
  -H 'cookie: YSC=test; SID=test123' \\
  -H 'x-goog-authuser: 0'"""

# Test 2: Fetch format
fetch_format = """fetch("https://music.youtube.com/youtubei/v1/browse", {
  "headers": {
    "accept": "*/*",
    "accept-language": "en-GB,en;q=0.9",
    "authorization": "SAPISIDHASH 123_test",
    "cookie": "YSC=test; SID=test123",
    "x-goog-authuser": "0"
  }
})"""

# Test 3: JSON format
json_format = """{
  "accept": "*/*",
  "accept-language": "en-GB,en;q=0.9",
  "authorization": "SAPISIDHASH 123_test",
  "cookie": "YSC=test; SID=test123",
  "x-goog-authuser": "0"
}"""

# Test 4: Newline separated (existing format)
newline_format = """accept
*/*
accept-language
en-GB,en;q=0.9
authorization
SAPISIDHASH 123_test
cookie
YSC=test; SID=test123
x-goog-authuser
0"""

# Test 5: Standard format
standard_format = """accept: */*
accept-language: en-GB,en;q=0.9
authorization: SAPISIDHASH 123_test
cookie: YSC=test; SID=test123
x-goog-authuser: 0"""

formats = [
    ("cURL", curl_format),
    ("Fetch", fetch_format),
    ("JSON", json_format),
    ("Newline-separated", newline_format),
    ("Standard", standard_format)
]

for name, test_input in formats:
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"{'='*80}")
    try:
        parsed = parse_headers(test_input)
        print(f"Parsed {len(parsed.split(chr(10)))} headers")
        is_valid, missing = validate_required_headers(parsed)
        if is_valid:
            print("✅ PASS - All required headers present")
        else:
            print(f"❌ FAIL - Missing: {missing}")
            print(f"Parsed output:\n{parsed}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
