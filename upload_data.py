import csv
import json
import time
import urllib.request
import urllib.error

API_URL = "https://eventflowai-production.up.railway.app/api/events"

print("Loading dataset using built-in csv module...")

events = []
with open("ml/data/raw/events_raw.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        if count >= 500:
            break
        events.append(row)
        count += 1

success = 0
failed = 0

print(f"Uploading {len(events)} events to your live database via Railway...")

for index, row in enumerate(events):
    payload = {
        "event_type": row['event_type'].lower() if row.get('event_type') else "unplanned",
        "latitude": float(row['latitude']) if row.get('latitude') else 12.9716,
        "longitude": float(row['longitude']) if row.get('longitude') else 77.5946,
        "address": row['address'] if row.get('address') else 'Unknown Location',
        "event_cause": str(row.get('event_cause', 'others')).lower().replace(' ', '_'),
        "requires_road_closure": str(row.get('requires_road_closure', 'false')).lower() == 'true',
        "start_datetime": row['start_datetime'] if row.get('start_datetime') else None,
        "priority": row.get('priority', 'Low'),
        "corridor": row.get('corridor', 'Non-corridor'),
        "zone": row.get('zone', 'Default Zone'),
        "description": row.get('description', 'No description provided')
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(API_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 201]:
                success += 1
            else:
                failed += 1
                print(f"Failed to insert row {index}: Status {response.status}")
    except urllib.error.URLError as e:
        failed += 1
        print(f"Error on row {index}: {str(e)}")
        
    time.sleep(0.05)

print("\n--- Upload Complete ---")
print(f"Successfully added: {success} dots to your live map!")
print(f"Failed: {failed}")
print("Go check your Vercel website now!")
