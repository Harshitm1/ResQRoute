import os
import requests
import folium        # For interactive map plotting
import polyline      # For decoding polyline strings
import openrouteservice  # Fallback routing library
from geopy.geocoders import Nominatim  # Fallback geocoding
import threading
import webbrowser
from flask import Flask, send_file

# ============================
# API Keys and Tokens
# ============================
MAPPLS_TOKEN = "9281693d-f6bc-4cc5-8090-e67a076211d1"  # Provided token
ORS_API_KEY = "5b3ce3597851110001cf6248d8d58b9a5e2049c28ad968512a1f393e"  # Your ORS key

# Determine the project root directory (one level up from the current file)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_FILE = os.path.join(BASE_DIR, "route_map.html")

# ======================================================
# 1️⃣ Mappls Geocoding: Get Coordinates
# ======================================================
def get_coords_mappls(location):
    """
    Uses Mappls API for geocoding.
    URL: https://atlas.mappls.com/api/places/geocode?
    Uses header 'Authorization: Bearer <MAPPLS_TOKEN>' and query parameter 'q'.
    Returns (latitude, longitude) on success.
    """
    try:
        url = "https://atlas.mappls.com/api/places/geocode?"
        headers = {
            "Authorization": f"Bearer {MAPPLS_TOKEN}"
        }
        params = {"q": location}
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code != 200:
            return None
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            lat = float(result["latitude"])
            lng = float(result["longitude"])
            return (lat, lng)
        return None
    except Exception as e:
        print("Error in Mappls geocoding:", e)
        return None

# ======================================================
# 2️⃣ MapmyIndia Routing: Get Route Details
# ======================================================
def get_route_mapmyindia(source_coords, dest_coords):
    """
    Uses MapmyIndia routing API.
    (For demonstration, the URL below is a placeholder. Replace with a valid endpoint if needed.)
    """
    try:
        # MapmyIndia expects coordinates as (lng, lat)
        src_lng, src_lat = source_coords[1], source_coords[0]
        dst_lng, dst_lat = dest_coords[1], dest_coords[0]
        # Example URL; adjust as necessary:
        url = f"https://apis.mappls.com/advancedmaps/v1/485a48aed1525c383bed11144b07ca6a/rev_geocode?lat={src_lat}&lng={src_lng}"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None
        data = response.json()
        # This endpoint is for reverse geocoding; in a real scenario, replace with the correct routing API.
        # For demonstration, we assume a dummy response structure:
        if "routes" in data and len(data["routes"]) > 0:
            route_info = data["routes"][0]
            distance_m = route_info["distance"]
            duration_s = route_info["duration"]
            geometry = route_info["geometry"]  # Encoded polyline string
            return {
                "distance_km": distance_m / 1000,
                "eta_minutes": duration_s / 60,
                "polyline": geometry
            }
        return None
    except Exception:
        return None

# ======================================================
# 3️⃣ Fallback Geocoding using OpenStreetMap (Geopy)
# ======================================================
def get_coords_fallback(location):
    geolocator = Nominatim(user_agent="resqroute")
    loc = geolocator.geocode(location, timeout=5)
    if loc:
        return (loc.latitude, loc.longitude)
    return None

# ======================================================
# 4️⃣ Fallback Routing using OpenRouteService
# ======================================================
def get_route_fallback(source_coords, dest_coords):
    client = openrouteservice.Client(key=ORS_API_KEY)
    # ORS expects coordinates as (lng, lat)
    coords = (source_coords[::-1], dest_coords[::-1])
    try:
        routes = client.directions(coords, profile='driving-car')
        route = routes['routes'][0]
        distance_m = route['summary']['distance']
        duration_s = route['summary']['duration']
        geometry = route['geometry']  # Encoded polyline string or GeoJSON geometry
        return {
            "distance_km": distance_m / 1000,
            "eta_minutes": duration_s / 60,
            "polyline": geometry
        }
    except Exception:
        return None

# ======================================================
# 5️⃣ Main function to get the optimized route
# ======================================================
def get_optimized_route(source, destination):
    # Attempt Mappls geocoding
    src_coords = get_coords_mappls(source)
    dst_coords = get_coords_mappls(destination)
    
    if not src_coords or not dst_coords:
        print("Mappls geocoding API does not work. Using fallback geocoding.")
        src_coords = get_coords_fallback(source)
        dst_coords = get_coords_fallback(destination)
        if not src_coords or not dst_coords:
            return {"error": "Failed to get coordinates from fallback as well."}
    
    # Attempt MapmyIndia routing (if available)
    route_info = get_route_mapmyindia(src_coords, dst_coords)
    
    if not route_info:
        print("MapmyIndia routing API does not work. Using fallback routing.")
        route_info = get_route_fallback(src_coords, dst_coords)
        if not route_info:
            return {"error": "Failed to get route from fallback as well."}
    
    route_info["source_coords"] = src_coords
    route_info["dest_coords"] = dst_coords
    return route_info

# ======================================================
# 6️⃣ Plot the route on a map with a green polyline
# ======================================================
def plot_route_on_map(route_info):
    if "error" in route_info:
        print(f"Error: {route_info['error']}")
        return

    geometry = route_info["polyline"]

    # Determine if geometry is GeoJSON (dict) or an encoded polyline (str)
    if isinstance(geometry, dict) and geometry.get("type") == "LineString":
        # Convert GeoJSON coordinates [lng, lat] to (lat, lng)
        route_points = [(coord[1], coord[0]) for coord in geometry["coordinates"]]
    elif isinstance(geometry, str):
        try:
            route_points = polyline.decode(geometry)
        except Exception as e:
            print("Failed to decode polyline:", e)
            route_points = [route_info["source_coords"], route_info["dest_coords"]]
    else:
        route_points = [route_info["source_coords"], route_info["dest_coords"]]

    if not route_points or len(route_points) == 0:
        route_points = [route_info["source_coords"], route_info["dest_coords"]]

    # Create a Folium map centered at the midpoint of the route
    midpoint = route_points[len(route_points) // 2]
    m = folium.Map(location=[midpoint[0], midpoint[1]], zoom_start=12)
    
    # Draw a green polyline along the route
    folium.PolyLine(route_points, color="green", weight=5, opacity=0.7).add_to(m)
    
    # Add markers for source and destination
    folium.Marker(location=route_info["source_coords"], popup="Source").add_to(m)
    folium.Marker(location=route_info["dest_coords"], popup="Destination").add_to(m)
    
    print(f"Distance (km): {route_info['distance_km']:.2f}")
    print(f"ETA (minutes): {route_info['eta_minutes']:.2f}")
    
    # Save the map in the project root directory
    m.save(MAP_FILE)
    print(f"Map has been saved as {MAP_FILE}")

# ======================================================
# 7️⃣ Flask App to Serve the Map on Host 5005
# ======================================================
app = Flask(__name__)

@app.route("/")
def display_map():
    return send_file(MAP_FILE)

def open_browser():
    webbrowser.open_new("http://localhost:5005/")

# ======================================================
# 8️⃣ Main Execution: Get Input, Generate Route, and Display Map
# ======================================================
if __name__ == "__main__":
    print("Enter the starting point:")
    source_location = input().strip()
    print("Enter the destination:")
    destination_location = input().strip()
    
    route_details = get_optimized_route(source_location, destination_location)
    plot_route_on_map(route_details)
    
    # Open the map in the default web browser after 1 second and run Flask on port 5005
    threading.Timer(1, open_browser).start()
    app.run(host="0.0.0.0", port=5005)

