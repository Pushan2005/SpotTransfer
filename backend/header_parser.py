
import re
import json

def extract_from_curl(text: str) -> dict:
    headers = {}

    cleaned = text.replace('^"', '"').replace('^', '')

    patterns = [
        r"(?:-H|--header)\s+['\"]([^:]+?):\s*([^'\"]+?)['\"]",
        r"(?:-H|--header)\s+([^:]+?):\s*([^\r\n]+?)(?:\s*\\|\s*\^|\s*$)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, cleaned, re.MULTILINE | re.IGNORECASE)
        for name, value in matches:
            clean_name = name.strip().lower()
            clean_value = value.strip().rstrip('\\').rstrip('^').strip()
            if clean_name and clean_value:
                headers[clean_name] = clean_value

    cookie_pattern = r"(?:-b|--cookie)\s+['\"]([^'\"]+)['\"]"

    matches = re.findall(cookie_pattern, cleaned, re.MULTILINE | re.IGNORECASE)
    for cookie_value in matches:
        clean_value = cookie_value.strip()
        if clean_value:
            if 'cookie' in headers:
                headers['cookie'] += '; ' + clean_value
            else:
                headers['cookie'] = clean_value

    return headers


def extract_from_fetch(text: str) -> dict:
    headers = {}
    headers_match = re.search(r'["\']?headers["\']?\s*:\s*\{([^}]+)\}', text, re.DOTALL)
    if headers_match:
        headers_obj = headers_match.group(1)
        pattern = r'["\']([^"\']+)["\']\s*:\s*["\']([^"\']+)["\']'
        matches = re.findall(pattern, headers_obj)
        for name, value in matches:
            headers[name.strip().lower()] = value.strip()
    return headers


def extract_from_json(text: str) -> dict:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return {k.lower(): v for k, v in data.items()}
    except:
        pass
    return {}


def parse_headers(raw_headers: str) -> str:
    if not raw_headers:
        return ""

    parsed_headers = {}

    if 'curl' in raw_headers.lower() or '-H ' in raw_headers or '--header' in raw_headers:
        curl_headers = extract_from_curl(raw_headers)
        if curl_headers:
            parsed_headers.update(curl_headers)

    if 'fetch(' in raw_headers or 'headers:' in raw_headers:
        fetch_headers = extract_from_fetch(raw_headers)
        if fetch_headers:
            parsed_headers.update(fetch_headers)

    if raw_headers.strip().startswith('{'):
        json_headers = extract_from_json(raw_headers)
        if json_headers:
            parsed_headers.update(json_headers)

    if parsed_headers:
        result_lines = []
        for name, value in parsed_headers.items():
            if name and name[0].isalpha():
                result_lines.append(f"{name}: {value}")
        if result_lines:
            return '\n'.join(result_lines)
    if 'Decoded:' in raw_headers or 'decoded:' in raw_headers.lower():
        lines_text = raw_headers.split('\n')
        cleaned_lines = []
        in_decoded_section = False
        brace_count = 0

        for line in lines_text:
            stripped = line.strip()

            if stripped.lower() == 'decoded:':
                in_decoded_section = True
                continue

            if in_decoded_section:
                brace_count += stripped.count('{')
                brace_count -= stripped.count('}')

                if brace_count <= 0 and '}' in stripped:
                    in_decoded_section = False
                continue

            cleaned_lines.append(line)

        raw_headers = '\n'.join(cleaned_lines)

    lines = raw_headers.strip().split('\n')
    parsed_headers = {}
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        if line.startswith(':'):
            i += 1
            continue

        if ': ' in line:
            parts = line.split(': ', 1)
            header_name = parts[0].strip().lower()
            header_value = parts[1].strip()
            parsed_headers[header_name] = header_value
            i += 1

        elif line.endswith(':'):
            header_name = line[:-1].strip().lower()
            if i + 1 < len(lines):
                header_value = lines[i + 1].strip()
                parsed_headers[header_name] = header_value
                i += 2
            else:
                i += 1

        elif '=' in line and not line.startswith('=') and ' ' not in line.split('=')[0]:
            parts = line.split('=', 1)
            header_name = parts[0].strip().lower()
            header_value = parts[1].strip()
            parsed_headers[header_name] = header_value
            i += 1

        elif i + 1 < len(lines):
            next_line = lines[i + 1].strip()

            def looks_like_header_name(s):
                if not s or s.startswith(':'):
                    return False
                if ';' in s or ', ' in s or ' ' in s:
                    return False
                clean = s.replace('-', '').replace('_', '')
                return clean.isalnum() and s[0].islower()

            def looks_like_header_value(s):
                if not s:
                    return False
                return (';' in s or ', ' in s or '/' in s or
                        s[0].isupper() or s[0].isdigit() or s[0] in ['*', '"', '?'])

            current_is_header = looks_like_header_name(line)
            next_is_value = looks_like_header_value(next_line)
            next_is_header = looks_like_header_name(next_line)

            if current_is_header and (next_is_value or not next_is_header):
                header_name = line.lower()
                header_value = next_line
                parsed_headers[header_name] = header_value
                i += 2
            else:
                i += 1
        else:
            i += 1

    result_lines = []
    for header_name, header_value in parsed_headers.items():
        if not header_name or not header_name[0].isalpha():
            continue
        if not all(c.isalnum() or c in ['-', '_'] for c in header_name):
            continue

        result_lines.append(f"{header_name}: {header_value}")

    return '\n'.join(result_lines)


def validate_required_headers(headers_str: str) -> tuple[bool, list[str]]:
    required_headers = {'cookie', 'x-goog-authuser'}

    headers_dict = {}
    for line in headers_str.split('\n'):
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers_dict[key.lower()] = value

    missing = required_headers - set(headers_dict.keys())

    return len(missing) == 0, list(missing)