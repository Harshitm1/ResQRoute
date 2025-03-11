import os
import time
import threading
import requests
import folium        # For interactive map plotting
import polyline      # For decoding polyline strings
import openrouteservice  # Fallback routing library
from geopy.geocoders import Nominatim  # Fallback geocoding
import webbrowser
from flask import Flask, send_file

##############################
#      SAFETY SCORE SIM      #
##############################
# Global variable for safety score simulation
TRAFFIC_LIGHT_SAFETY = "RED"
CRITICAL_BP = 90
CRITICAL_SPO2 = 92
CRITICAL_HR = 50

def check_vital_signs_safety(bp, spo2, hr):
    global TRAFFIC_LIGHT_SAFETY
    if bp < CRITICAL_BP or spo2 < CRITICAL_SPO2 or hr < CRITICAL_HR:
        TRAFFIC_LIGHT_SAFETY = "GREEN"
    else:
        TRAFFIC_LIGHT_SAFETY = "RED"

def run_safety_score_simulation():
    print("\n=== Safety Score Simulation ===")
    while True:
        bp = input("Enter Blood Pressure (or type 'exit' to finish): ")
        if bp.lower() == "exit":
            break
        spo2 = input("Enter SpO2: ")
        if spo2.lower() == "exit":
            break
        hr = input("Enter Heart Rate: ")
        if hr.lower() == "exit":
            break
        try:
            bp, spo2, hr = int(bp), int(spo2), int(hr)
        except:
            print("Invalid input. Please enter numeric values.")
            continue
        check_vital_signs_safety(bp, spo2, hr)
        print("Safety Score:", "High Risk" if TRAFFIC_LIGHT_SAFETY == "GREEN" else "Normal")
        print("Current Safety Simulation Traffic Light:", TRAFFIC_LIGHT_SAFETY)
        time.sleep(1)
    print("Safety Score Simulation completed.\n")

##############################
#    ROUTE OPTIMIZER SIM     #
##############################
# (Assuming MAPPLS token is provided and ORS key is valid.)
MAPPLS_TOKEN = "9281693d-f6bc-4cc5-8090-e67a076211d1"
ORS_API_KEY = "5b3ce3597851110001cf6248d8d58b9a5e2049c28ad968512a1f393e"

# Determine project root (one level up from this file's directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_FILE = os.path.join(BASE_DIR, "route_map.html")

def get_coords_mappls(location):
    """Uses Mappls API for geocoding."""
    try:
        url = "https://atlas.mappls.com/api/places/geocode?"
        headers = {"Authorization": f"Bearer {MAPPLS_TOKEN}"}
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

def get_route_mapmyindia(source_coords, dest_coords):
    """
    Dummy function for routing using MapmyIndia.
    (This endpoint is a placeholder; routing is attempted via fallback if this fails.)
    """
    try:
        # MapmyIndia expects (lng, lat)
        src_lng, src_lat = source_coords[1], source_coords[0]
        dst_lng, dst_lat = dest_coords[1], dest_coords[0]
        # Placeholder URL; in real usage, update with a valid endpoint.
        url = f"https://apis.mappls.com/advancedmaps/v1/YOUR_MAPMYINDIA_API_KEY/rev_geocode?lat={src_lat}&lng={src_lng}"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None
        data = response.json()
        if "routes" in data and len(data["routes"]) > 0:
            route_info = data["routes"][0]
            distance_m = route_info["distance"]
            duration_s = route_info["duration"]
            geometry = route_info["geometry"]
            return {
                "distance_km": distance_m / 1000,
                "eta_minutes": duration_s / 60,
                "polyline": geometry
            }
        return None
    except Exception:
        return None

def get_coords_fallback(location):
    geolocator = Nominatim(user_agent="resqroute")
    loc = geolocator.geocode(location, timeout=5)
    return (loc.latitude, loc.longitude) if loc else None

def get_route_fallback(source_coords, dest_coords):
    client = openrouteservice.Client(key=ORS_API_KEY)
    # ORS expects coordinates as (lng, lat)
    coords = (source_coords[::-1], dest_coords[::-1])
    try:
        routes = client.directions(coords, profile='driving-car')
        route = routes['routes'][0]
        distance_m = route['summary']['distance']
        duration_s = route['summary']['duration']
        geometry = route['geometry']
        return {
            "distance_km": distance_m / 1000,
            "eta_minutes": duration_s / 60,
            "polyline": geometry
        }
    except Exception:
        return None

def get_optimized_route(source, destination):
    src_coords = get_coords_mappls(source)
    dst_coords = get_coords_mappls(destination)
    if not src_coords or not dst_coords:
        print("Mappls geocoding API does not work. Using fallback geocoding.")
        src_coords = get_coords_fallback(source)
        dst_coords = get_coords_fallback(destination)
        if not src_coords or not dst_coords:
            return {"error": "Failed to get coordinates from fallback."}
    route_info = get_route_mapmyindia(src_coords, dst_coords)
    if not route_info:
        print("MapmyIndia routing API does not work. Using fallback routing.")
        route_info = get_route_fallback(src_coords, dst_coords)
        if not route_info:
            return {"error": "Failed to get route from fallback."}
    route_info["source_coords"] = src_coords
    route_info["dest_coords"] = dst_coords
    return route_info

def plot_route_on_map(route_info):
    if "error" in route_info:
        print(f"Error: {route_info['error']}")
        return
    geometry = route_info["polyline"]
    if isinstance(geometry, dict) and geometry.get("type") == "LineString":
        route_points = [(coord[1], coord[0]) for coord in geometry["coordinates"]]
    elif isinstance(geometry, str):
        try:
            route_points = polyline.decode(geometry)
        except Exception as e:
            print("Failed to decode polyline:", e)
            route_points = [route_info["source_coords"], route_info["dest_coords"]]
    else:
        route_points = [route_info["source_coords"], route_info["dest_coords"]]
    if not route_points:
        route_points = [route_info["source_coords"], route_info["dest_coords"]]
    midpoint = route_points[len(route_points) // 2]
    m = folium.Map(location=[midpoint[0], midpoint[1]], zoom_start=12)
    folium.PolyLine(route_points, color="green", weight=5, opacity=0.7).add_to(m)
    folium.Marker(location=route_info["source_coords"], popup="Source").add_to(m)
    folium.Marker(location=route_info["dest_coords"], popup="Destination").add_to(m)
    print(f"Distance (km): {route_info['distance_km']:.2f}")
    print(f"ETA (minutes): {route_info['eta_minutes']:.2f}")
    m.save(MAP_FILE)
    print(f"Map saved as {MAP_FILE}")

def run_route_optimizer_simulation():
    print("\n=== Route Optimizer Simulation ===")
    source = input("Enter starting point: ").strip()
    destination = input("Enter destination: ").strip()
    route_details = get_optimized_route(source, destination)
    plot_route_on_map(route_details)
    # Start Flask server to serve the map
    def open_browser():
        webbrowser.open_new("http://localhost:5005/")
    threading.Timer(1, open_browser).start()
    app = Flask(__name__)
    @app.route("/")
    def display_map():
        return send_file(MAP_FILE)
    app.run(host="0.0.0.0", port=5005)

##############################
#     IOT TRAFFIC SIM        #
##############################
TRAFFIC_LIGHT_IOT = "RED"
CRITICAL_BP1 = 90
CRITICAL_BP2 = 140
CRITICAL_SPO2_IOT = 92
CRITICAL_HR1 = 50
CRITICAL_HR2 = 120

def check_vital_signs_iot(bp, spo2, hr):
    global TRAFFIC_LIGHT_IOT
    if bp < CRITICAL_BP1 or bp > CRITICAL_BP2 or spo2 < CRITICAL_SPO2_IOT or hr < CRITICAL_HR1 or hr > CRITICAL_HR2:
        TRAFFIC_LIGHT_IOT = "GREEN"
        print("EMERGENCY DETECTED! Traffic Light turned GREEN for ambulance!")
    else:
        TRAFFIC_LIGHT_IOT = "RED"
        print("Patient stable. Traffic Light remains RED.")

def run_iot_traffic_simulation():
    print("\n=== IoT Traffic Simulation ===")
    while True:
        bp = input("Enter Blood Pressure (or type 'exit' to finish): ")
        if bp.lower() == "exit":
            break
        spo2 = input("Enter SpO2: ")
        if spo2.lower() == "exit":
            break
        hr = input("Enter Heart Rate: ")
        if hr.lower() == "exit":
            break
        try:
            bp, spo2, hr = int(bp), int(spo2), int(hr)
        except:
            print("Invalid input, try again.")
            continue
        check_vital_signs_iot(bp, spo2, hr)
        print("Current IoT Traffic Light Status:", TRAFFIC_LIGHT_IOT)
        time.sleep(1)
    print("IoT Traffic Simulation completed.\n")

##############################
#           MAIN             #
##############################
def main():
    print("Integrated Simulation: Safety Score -> Route Optimizer -> IoT Traffic Simulation")
    input("Press Enter to start Safety Score Simulation...")
    # Run Safety Score Simulation
    run_safety_score_simulation()
    
    input("Press Enter to start Route Optimizer Simulation...")
    # Run Route Optimizer Simulation (this will block until Flask is terminated)
    run_route_optimizer_simulation()
    
    input("Press Enter to start IoT Traffic Simulation...")
    # Run IoT Traffic Simulation
    run_iot_traffic_simulation()

if __name__ == "__main__":
    main()

