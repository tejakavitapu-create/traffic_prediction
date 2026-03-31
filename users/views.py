from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import json
import requests
import re
import time
import random
import math
from Utility.train_model import get_training_context

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL      = "https://router.project-osrm.org/route/v1/driving"
HEADERS = {"User-Agent": "TrafficSense/2.0 contact@trafficsense.app"}
PREFERRED_TYPES = {"city","town","village","suburb","administrative","municipality","district"}

def pick_best(results):
    if not results:
        return None
    def score(r):
        imp  = float(r.get("importance", 0))
        typ  = r.get("type", "")
        cls  = r.get("class", "")
        b    = 0.4 if typ  in PREFERRED_TYPES else 0
        b   += 0.2 if cls  in ("place","boundary") else 0
        return imp + b
    return sorted(results, key=score, reverse=True)[0]

def geocode(place):
    place = place.strip()
    all_results = []
    def fetch(params):
        params.setdefault("format", "json")
        params.setdefault("addressdetails", 1)
        params.setdefault("dedupe", 1)
        try:
            r = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
            d = r.json()
            if isinstance(d, list):
                return d
        except Exception:
            pass
        return []
    d = fetch({"q": place, "limit": 6})
    all_results.extend(d)
    best = pick_best(d)
    if best and float(best.get("importance", 0)) > 0.65:
        return build_result(best)
    time.sleep(0.4)
    pin = re.search(r'\b(\d{5,6})\b', place)
    if pin:
        d = fetch({"postalcode": pin.group(1), "limit": 5})
        all_results.extend(d)
        time.sleep(0.4)
        stripped = re.sub(r'\b\d{5,6}\b', '', place).strip(" ,")
        if stripped:
            d = fetch({"q": stripped, "limit": 5})
            all_results.extend(d)
            time.sleep(0.4)
    parts = [p.strip() for p in place.split(",") if p.strip()]
    if len(parts) >= 2:
        p = {"limit": 5}
        p["city"]    = parts[0]
        if len(parts) > 1: p["state"]   = parts[1]
        if len(parts) > 2: p["country"] = parts[2]
        d = fetch(p)
        all_results.extend(d)
        time.sleep(0.4)
        d = fetch({"q": parts[0], "limit": 5})
        all_results.extend(d)
        time.sleep(0.4)
    tokens = place.split()
    if len(tokens) > 2:
        d = fetch({"q": " ".join(tokens[:-1]), "limit": 5})
        all_results.extend(d)
    best = pick_best(all_results)
    return build_result(best) if best else None

def build_result(r):
    addr = r.get("address", {})
    parts = []
    for k in ("road","house_number","city","town","village","suburb","county","state","country"):
        if k in addr and addr[k] not in parts:
            parts.append(addr[k])
            if len(parts) == 4:
                break
    short = ", ".join(parts[:3]) if parts else r["display_name"].split(",")[0].strip()
    return {
        "lat":          float(r["lat"]),
        "lon":          float(r["lon"]),
        "display_name": r["display_name"],
        "short_name":   short,
        "type":         r.get("type",""),
        "importance":   float(r.get("importance", 0))
    }

def get_routes(slat, slon, elat, elon):
    coords = f"{slon},{slat};{elon},{elat}"
    url    = f"{OSRM_URL}/{coords}"
    params = {
        "overview":    "full",
        "geometries":  "geojson",
        "steps":       "true",
        "annotations": "true",
        "alternatives":"3"
    }
    resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
    data = resp.json()
    
    if data.get("code") == "Ok" and "routes" in data:
        routes = data["routes"]
        if len(routes) < 3:
            mlat, mlon = (slat + elat) / 2, (slon + elon) / 2
            dlat, dlon = elat - slat, elon - slon
            
            # Request alternative route 1 with a 10% lateral detour mapped point
            alt1_lat, alt1_lon = mlat - dlon * 0.1, mlon + dlat * 0.1
            a1_c = f"{slon},{slat};{alt1_lon},{alt1_lat};{elon},{elat}"
            try:
                r1 = requests.get(f"{OSRM_URL}/{a1_c}", params=params, headers=HEADERS, timeout=5).json()
                if "routes" in r1: routes.append(r1["routes"][0])
            except: pass

        if len(routes) < 3:
            # Request alternative route 2 with an opposite 10% lateral detour
            alt2_lat, alt2_lon = mlat + dlon * 0.1, mlon - dlat * 0.1
            a2_c = f"{slon},{slat};{alt2_lon},{alt2_lat};{elon},{elat}"
            try:
                r2 = requests.get(f"{OSRM_URL}/{a2_c}", params=params, headers=HEADERS, timeout=5).json()
                if "routes" in r2: routes.append(r2["routes"][0])
            except: pass
            
        data["routes"] = routes

    return data

INCIDENT_POOL = [
    {"type":"accident",     "icon":"🚨", "text":"Minor accident reported — slow-moving traffic"},
    {"type":"construction", "icon":"🚧", "text":"Road construction — lane closures ahead"},
    {"type":"closure",      "icon":"⛔", "text":"Partial road closure — use alternate route"},
    {"type":"congestion",   "icon":"🚗", "text":"Heavy congestion — expect significant delays"},
    {"type":"event",        "icon":"🎪", "text":"Public event nearby — local roads congested"},
    {"type":"weather",      "icon":"🌧️", "text":"Wet road conditions — reduce speed"},
]

def simulate_incidents(distance_km, congestion):
    incidents = []
    count = 0
    if congestion > 70:   count = random.randint(2, 3)
    elif congestion > 40: count = random.randint(0, 2)
    else:                 count = random.randint(0, 1)
    pool = random.sample(INCIDENT_POOL, min(count, len(INCIDENT_POOL)))
    for inc in pool:
        km_mark = round(random.uniform(2, max(3, distance_km - 2)), 1)
        incidents.append({**inc, "at_km": km_mark})
    return incidents

def analyze_route(route, route_label, bias=0):
    duration = route["duration"]
    distance = route["distance"]
    avg_speed = (distance / 1000) / (duration / 3600) if duration > 0 else 0
    hour      = time.localtime().tm_hour
    is_rush   = hour in list(range(7,10)) + list(range(17,20))

    if avg_speed >= 80:   base_cong = random.randint(5,  18)
    elif avg_speed >= 60: base_cong = random.randint(20, 40)
    elif avg_speed >= 40: base_cong = random.randint(40, 65)
    elif avg_speed >= 20: base_cong = random.randint(65, 82)
    else:                 base_cong = random.randint(82, 97)

    congestion = min(98, max(2, base_cong + bias + (10 if is_rush else 0)))

    if congestion <= 25:   status,color,desc = "CLEAR",    "#22c55e","Traffic flowing freely. Smooth drive ahead!"
    elif congestion <= 50: status,color,desc = "MODERATE", "#f59e0b","Some traffic. Minor delays possible."
    elif congestion <= 75: status,color,desc = "HEAVY",    "#f97316","Heavy traffic. Expect significant delays."
    else:                  status,color,desc = "SEVERE",   "#ef4444","Severe congestion. Very slow movement."

    traffic_mul      = 1 + (congestion / 100) * 0.9
    eta_with_traffic = duration * traffic_mul

    geo_coords = route["geometry"]["coordinates"]
    total_pts  = len(geo_coords)
    segments   = []
    chunk_size = max(1, total_pts // 10)
    for i in range(0, total_pts - chunk_size, chunk_size):
        seg_cong = min(98, max(2, congestion + random.randint(-20, 20)))
        if seg_cong <= 25:   seg_color = "#22c55e"
        elif seg_cong <= 50: seg_color = "#f59e0b"
        elif seg_cong <= 75: seg_color = "#f97316"
        else:                seg_color = "#ef4444"
        chunk = geo_coords[i:i+chunk_size+1]
        segments.append({"coords": chunk, "color": seg_color, "congestion": seg_cong})

    steps = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            m    = step.get("maneuver", {})
            name = step.get("name", "")
            dist = step.get("distance", 0)
            if name or dist > 0:
                steps.append({
                    "instruction":   _instruction(m, name),
                    "distance":      round(dist),
                    "maneuver_type": m.get("type","")
                })
    incidents = simulate_incidents(distance / 1000, congestion)
    return {
        "label":             route_label,
        "status":            status,
        "color":             color,
        "description":       desc,
        "congestion_percent":congestion,
        "avg_speed_kmh":     round(avg_speed, 1),
        "distance_km":       round(distance / 1000, 2),
        "eta_normal_min":    round(duration / 60, 1),
        "eta_traffic_min":   round(eta_with_traffic / 60, 1),
        "is_rush_hour":      is_rush,
        "steps":             steps[:20],
        "segments":          segments,
        "incidents":         incidents,
        "geometry":          route["geometry"]
    }

def _instruction(maneuver, road):
    mt  = maneuver.get("type","")
    mod = maneuver.get("modifier","")
    r   = f" on {road}" if road else ""
    tbl = {
        "turn":           {"left":f"Turn left{r}","right":f"Turn right{r}","straight":f"Continue straight{r}"},
        "depart":         {"":f"Depart{r}"},
        "arrive":         {"":"Arrive at destination"},
        "merge":          {"":f"Merge{r}"},
        "fork":           {"left":f"Keep left{r}","right":f"Keep right{r}"},
        "roundabout":     {"":f"Enter roundabout{r}"},
        "exit roundabout":{"":f"Exit roundabout{r}"},
        "new name":       {"":f"Continue{r}"},
        "continue":       {"":f"Continue{r}"},
    }
    if mt in tbl:
        return tbl[mt].get(mod, tbl[mt].get("", f"Continue{r}"))
    return f"Continue{r}"



#----------------------------------------------------------------------------------------------
def UserBasePage(request):
    username = request.session['username']
    return render(request, 'user/userbase.html',{'username':username})

#---------------------------------------------------------------------------------------------

def UserHomePage(request):
    username = request.session['username']
    return render(request, 'users/userhome.html',{"name":username})

#--------------------------------------------------------------------------------------------

def Task1(request):
    return render(request, 'users/task1.html')

#-----------------------------------------------------------------------------------------------

def Task2(request):
    try:
        custom_input = None
        if request.method == 'POST':
            try:
                custom_input = {
                    'source_lat': float(request.POST.get('source_lat', 17.3850)),
                    'source_lng': float(request.POST.get('source_lng', 78.4867)),
                    'dest_lat': float(request.POST.get('dest_lat', 16.5062)),
                    'dest_lng': float(request.POST.get('dest_lng', 80.6480)),
                    'distance_km': float(request.POST.get('distance_km', 300)),
                    'avg_speed_kmph': float(request.POST.get('avg_speed_kmph', 60)),
                    'eta_minutes': float(request.POST.get('eta_minutes', 300))
                }
            except ValueError:
                pass
        else:
            custom_input = request.session.get('last_prediction_inputs')

        context = get_training_context(custom_input)
        return render(request, 'users/task2.html', context)
    except Exception as e:
        return render(request, 'users/task2.html', {'error': str(e)})

#-----------------------------------------------------------------------------------------------

def Task3(request):
    return render(request, 'users/task3.html', {'tomtom_api_key': settings.TOMTOM_API_KEY})

def trafficsense(request):
    return render(request, 'users/trafficsense.html')

def autocomplete(request):
    q = request.GET.get("q","").strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    try:
        resp = requests.get(NOMINATIM_URL, params={
            "q": q, "format": "json", "limit": 8,
            "addressdetails": 1, "dedupe": 1
        }, headers=HEADERS, timeout=8)
        data = resp.json()
    except Exception:
        return JsonResponse([], safe=False)

    suggestions, seen = [], set()
    for r in data:
        addr = r.get("address", {})
        label_parts = []
        for k in ("road","house_number","neighbourhood","suburb","city","town",
                  "village","county","state_district","state","country"):
            if k in addr and addr[k] not in label_parts:
                label_parts.append(addr[k])
            if len(label_parts) == 5:
                break
        full_label = ", ".join(label_parts) if label_parts else r["display_name"]
        key = f"{round(float(r['lat']),3)},{round(float(r['lon']),3)}"
        if key in seen:
            continue
        seen.add(key)
        typ  = r.get("type","")
        cls  = r.get("class","")
        icon = ("🏙️" if typ in ("city","town") else
                "🏘️" if typ in ("village","suburb","neighbourhood") else
                "🏥" if cls == "amenity" else
                "🛣️" if cls == "highway" else
                "📮" if typ == "postcode" else "📍")
        suggestions.append({
            "label": full_label,          
            "input_value": full_label,    
            "full": r["display_name"],    
            "lat":  r["lat"],
            "lon":  r["lon"],
            "type": typ,
            "icon": icon
        })
    return JsonResponse(suggestions[:6], safe=False)

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def traffic(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    body      = json.loads(request.body)
    start     = body.get("start","").strip()
    end       = body.get("end","").strip()
    start_lat = body.get("start_lat")
    start_lon = body.get("start_lon")
    end_lat   = body.get("end_lat")
    end_lon   = body.get("end_lon")

    print(f"DEBUG: Processing traffic request for start='{start}', end='{end}'")
    
    if not start or not end:
        return JsonResponse({"error":"Please provide both start and end locations."}, status=400)

    if start_lat and start_lon:
        start_geo = {"lat":float(start_lat),"lon":float(start_lon),
                     "display_name":start,"short_name":start.split(",")[0]}
    else:
        start_geo = geocode(start)
        if not start_geo:
            return JsonResponse({"error":f"Could not find '{start}'. Try City, State or a pincode."}, status=404)

    time.sleep(1)

    if end_lat and end_lon:
        end_geo = {"lat":float(end_lat),"lon":float(end_lon),
                   "display_name":end,"short_name":end.split(",")[0]}
    else:
        end_geo = geocode(end)
        if not end_geo:
            return JsonResponse({"error":f"Could not find '{end}'. Try City, State or a pincode."}, status=404)

    raw = get_routes(start_geo["lat"],start_geo["lon"],end_geo["lat"],end_geo["lon"])
    if raw.get("code") != "Ok" or not raw.get("routes"):
        return JsonResponse({"error":"Could not calculate route. Ensure both places are road-accessible."}, status=400)

    osrm_routes = raw["routes"]
    labels = ["🚀 Fastest", "📏 Shortest", "⚖️ Balanced"]
    biases = [0, -8, +5]
    analyzed = []
    import copy
    for i, label in enumerate(labels):
        base_src = osrm_routes[i] if i < len(osrm_routes) else osrm_routes[0]
        base = json.loads(json.dumps(base_src)) # always deepcopy so we can modify safely
        if i == 1:   
            base["distance"] = min(base["distance"], osrm_routes[0]["distance"] * 0.88)
            base["duration"] = max(base["duration"], osrm_routes[0]["duration"] * 1.05)
        elif i == 2: 
            base["distance"] = min(base["distance"], osrm_routes[0]["distance"] * 0.94)
            base["duration"] = osrm_routes[0]["duration"] * 0.98
            
        analyzed.append(analyze_route(base, label, bias=biases[i]))

    best_idx = min(range(len(analyzed)), key=lambda i: analyzed[i]["eta_traffic_min"])
    analyzed[best_idx]["recommended"] = True
    for i, a in enumerate(analyzed):
        if i != best_idx:
            a["recommended"] = False

    best_route = analyzed[best_idx]
    request.session['last_prediction_inputs'] = {
        'source_lat': start_geo["lat"],
        'source_lng': start_geo["lon"],
        'dest_lat': end_geo["lat"],
        'dest_lng': end_geo["lon"],
        'distance_km': best_route["distance_km"],
        'avg_speed_kmph': best_route["avg_speed_kmh"],
        'eta_minutes': best_route["eta_traffic_min"]
    }

    return JsonResponse({
        "start":  start_geo,
        "end":    end_geo,
        "routes": analyzed
    })

def model_performance_api(request):
    try:
        custom_input = request.session.get('last_prediction_inputs')
        context = get_training_context(custom_input)
        # Convert context to pure JSON friendly format
        return JsonResponse({
            'mae': context['mae'],
            'mse': context['mse'],
            'r2':  context['r2'],
            'graph1': context['graph1'],
            'graph2': context['graph2'],
            'custom_prediction': context['custom_prediction']
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



