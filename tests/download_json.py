#!/usr/bin/env python3
"""
Download JSON data from a URL and optionally save it to a file.

Usage:
    python download_json.py <url> [output_file]

Examples:
    python download_json.py https://api.example.com/data
    python download_json.py https://api.example.com/data output.json
"""

import sys
import json
import urllib.request
import urllib.error


def download_json(url: str, headers: dict = None) -> dict | list:
    """
    Download and parse JSON from the given URL.

    Args:
        url:     The URL to fetch.
        headers: Optional dict of HTTP headers (e.g. {"Authorization": "Bearer ..."}).

    Returns:
        Parsed JSON as a dict or list.

    Raises:
        urllib.error.URLError: On network/connection errors.
        json.JSONDecodeError:  If the response is not valid JSON.
    """
    req = urllib.request.Request(url, headers=headers or {})
    req.add_header("User-Agent", "python-json-downloader/1.0")

    with urllib.request.urlopen(req, timeout=10) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(raw.decode(charset))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Fetching: {url}")

    try:
        data = download_json(url)
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response: {e}", file=sys.stderr)
        sys.exit(1)

    pretty = json.dumps(data, indent=2, ensure_ascii=False)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(pretty)
        print(f"Saved to: {output_file}")
    else:
        print(pretty)


if __name__ == "__main__":
    main()