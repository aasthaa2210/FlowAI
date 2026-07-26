import requests
from config import ORS_API_KEY

def get_route(source_coords, dest_coords):
    """
    source_coords = [longitude, latitude]
    dest_coords   = [longitude, latitude]
    """
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }
    
    body = {
        "coordinates": [source_coords, dest_coords]
    }
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=15)
    except requests.exceptions.Timeout:
        raise Exception(
            "OpenRouteService did not respond within 15 seconds. "
            "Check your internet connection, or that api.openrouteservice.org "
            "isn't blocked by a firewall/VPN."
        )
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Couldn't connect to OpenRouteService. Check your internet connection."
        )

    try:
        data = response.json()
    except ValueError:
        raise Exception(
            f"OpenRouteService returned a non-JSON response (HTTP {response.status_code}). "
            "This usually means a firewall/proxy/VPN is intercepting the request, "
            "or the API key in config.py is invalid."
        )

    if response.status_code != 200 or "features" not in data or not data["features"]:
        error_msg = data.get("error", {})
        if isinstance(error_msg, dict):
            error_msg = error_msg.get("message", str(data))
        raise Exception(f"OpenRouteService error ({response.status_code}): {error_msg}")

    feature = data["features"][0]

    # Extract distance and duration
    summary = feature["properties"]["summary"]
    distance_km = round(summary["distance"] / 1000, 2)
    duration_min = round(summary["duration"] / 60, 1)

    # Road geometry for drawing on a map: list of [lng, lat] pairs
    geometry = feature["geometry"]["coordinates"]
    
    # Calculate congestion index (simple formula for now)
    expected_min = (distance_km / 40) * 60  # assuming 40km/h free flow
    congestion_index = round((duration_min / expected_min) * 5, 1)
    congestion_index = min(congestion_index, 10)  # cap at 10
    
    # Recommendation
    if congestion_index <= 3:
        level = "LOW 🟢"
        advice = "Good to go. Clear roads."
    elif congestion_index <= 6:
        level = "MEDIUM 🟡"
        advice = "Moderate traffic. Allow extra time."
    elif congestion_index <= 8:
        level = "HIGH 🟠"
        advice = "Heavy traffic. Consider alternate route."
    else:
        level = "VERY HIGH 🔴"
        advice = "Avoid this route. Major congestion."
    
    return {
        "distance_km": distance_km,
        "duration_min": duration_min,
        "congestion_index": congestion_index,
        "traffic_level": level,
        "advice": advice,
        "geometry": geometry  # list of [lng, lat] pairs, for drawing the route on a map
    }

# Test with Ahmedabad locations
if __name__ == "__main__":
    # Satellite to Maninagar (Ahmedabad)
    source = [72.5714, 23.0395]  # Satellite
    dest   = [72.6019, 22.9961]  # Maninagar
    
    result = get_route(source, dest)
    
    print("=== FlowAI Route Analysis ===")
    print(f"Distance     : {result['distance_km']} km")
    print(f"Duration     : {result['duration_min']} min")
    print(f"Congestion   : {result['congestion_index']} / 10")
    print(f"Traffic Level: {result['traffic_level']}")
    print(f"Advice       : {result['advice']}")

if __name__ == "__main__":
    print("=== FlowAI Route Analysis ===")
    print("Enter coordinates for Ahmedabad locations")
    print("")
    
    slat = float(input("Source Latitude  : "))
    slng = float(input("Source Longitude : "))
    dlat = float(input("Dest Latitude    : "))
    dlng = float(input("Dest Longitude   : "))
    
    result = get_route([slng, slat], [dlng, dlat])
    
    print("")
    print(f"Distance     : {result['distance_km']} km")
    print(f"Duration     : {result['duration_min']} min")
    print(f"Congestion   : {result['congestion_index']} / 10")
    print(f"Traffic Level: {result['traffic_level']}")
    print(f"Advice       : {result['advice']}")