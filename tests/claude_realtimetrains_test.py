"""
Fetch arrivals and departures from Derby Rail Station
using the Realtime Trains (RTT) API (data.rtt.io).

Credentials: https://api.rtt.io
"""

import json
import urllib.request
import urllib.error
import urllib.parse

RTT_CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZWRhNDRkYi1hYzJkLTRmMjItOGY2OC0wMDNlNjIwMmYzNDQiLCJpc3MiOiJodHRwczovL2FwaS1wb3J0YWwucnR0LmlvIn0.kx7ltkUpFNEH3NFwSX2BnwJ5ZMo-R01dvmgETaildCE"  # the long eyJ... token from your RTT portal
STATION_CODE = "NOT"  # Derby

def get_service_stops(access_token: str, unique_identity: str) -> list:
    url = f"https://data.rtt.io/gb-nr/service?version=2026-04-17&uniqueIdentity={unique_identity}"
    
    try:
        data = download_json_bearer(url, access_token)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise

    stops = []
    for location in data.get("service", {}).get("locations", []):
        temporal = location.get("temporalData", {})
        arrival = temporal.get("arrival", {}).get("scheduleAdvertised", "")
        departure = temporal.get("departure", {}).get("scheduleAdvertised", "")
        
        stops.append({
            "station": location.get("location", {}).get("description", "Unknown"),
            "arrival": arrival[11:16] if len(arrival) >= 16 else None,
            "departure": departure[11:16] if len(departure) >= 16 else None,
        })
    
    return stops


def get_access_token(client_token: str) -> str:
    url = "https://data.rtt.io/api/get_access_token"
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {client_token}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("User-Agent", "python-rtt-client/1.0")

    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
        #print(result)  # temporary - so we can see the response structure
        return result["token"]


def download_json_bearer(url: str, token: str) -> dict:
    """Fetch JSON from a URL using Bearer token auth."""
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "python-rtt-client/1.0")

    with urllib.request.urlopen(req, timeout=10) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(raw.decode(charset))


def get_station_data(station_code: str) -> tuple[dict, str]:
    """Returns (data, access_token) so the token can be reused."""
    access_token = get_access_token(RTT_CLIENT_TOKEN)
    url = f"https://data.rtt.io/gb-nr/location?version=2026-04-17&code={station_code}&timeTolerance=false&detailed=false&stpFilter=WVS"
    return download_json_bearer(url, access_token), access_token


def display_services(data: dict, access_token: str):
    """Print a simple summary of all services at the station."""
    query = data.get("query", {})
    location = query.get("location", {})
    print(f"\nStation: {location.get('description', 'Unknown')}")
    print(f"Showing: {query.get('timeFrom', '')} to {query.get('timeTo', '')}\n")

    services = data.get("services", [])
    if not services:
        print("No services found.")
        return

    print(f"{'Time':<8} {'Type':<6} {'Origin/Destination':<30} {'Operator':<25} {'Platform':<10} {'Status'}")
    print("-" * 100)

    for svc in services:
        temporal = svc.get("temporalData", {})
        meta = svc.get("scheduleMetadata", {})
        loc_meta = svc.get("locationMetadata", {})
        if meta.get("modeType") == "BUS":
            continue

        # Arrival or departure time
        if "departure" in temporal:
            time_data = temporal["departure"]
            time_type = "DEP"
            endpoints = svc.get("destination", [{}])
        else:
            time_data = temporal.get("arrival", {})
            time_type = "ARR"
            endpoints = svc.get("origin", [{}])

        # Parse time from ISO string e.g. "2026-04-20T13:45:00"
        scheduled = time_data.get("scheduleAdvertised", "")
        time_str = scheduled[11:16] if len(scheduled) >= 16 else "?"

        # Realtime forecast
        realtime = time_data.get("realtimeForecast", "")
        realtime_str = realtime[11:16] if len(realtime) >= 16 else None

        # Origin or destination name
        endpoint_name = "Unknown"
        if endpoints:
            endpoint_name = endpoints[0].get("location", {}).get("description", "Unknown")

        operator = meta.get("operator", {}).get("name", "Unknown")
        mode = meta.get("modeType", "TRAIN")  # TRAIN or BUS
        platform = loc_meta.get("platform", {}).get("forecast") or loc_meta.get("platform", {}).get("planned") or "-"

        cancelled = time_data.get("isCancelled", False)
        if cancelled:
            status = "CANCELLED"
        elif realtime_str and realtime_str != time_str:
            status = f"Exp {realtime_str}"
        else:
            status = "On time"

        print(f"{time_str:<8} {f'{time_type}/{mode}':<6} {endpoint_name:<30} {operator:<25} {str(platform):<10} {status}")

        unique_identity = meta.get("uniqueIdentity", "")  # "gb-nr:Y12346:2026-04-20"
        unique_identity = unique_identity.replace("gb-nr:", "")  # "Y12346:2026-04-20"
        encoded = urllib.parse.quote(unique_identity, safe="")  # "Y12346%3A2026-04-20"
        stops = get_service_stops(access_token, encoded)
        for stop in stops:
            arr = stop["arrival"] or "     "
            dep = stop["departure"] or "     "
            print(f"  {arr} / {dep}  {stop['station']}")

"""if __name__ == "__main__":
    try:
        data = get_station_data(STATION_CODE)
        import json
        print(json.dumps(data, indent=2))  # dump full response so we can see the structure
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.reason}")
        print(e.read().decode())"""

if __name__ == "__main__":
    try:
        access_token = get_access_token(RTT_CLIENT_TOKEN)
        url = f"https://data.rtt.io/gb-nr/location?version=2026-04-17&code={STATION_CODE}&timeTolerance=false&detailed=false&stpFilter=WVS"
        data, access_token = get_station_data(STATION_CODE)
        display_services(data, access_token)
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.reason}")
        print(e.read().decode())