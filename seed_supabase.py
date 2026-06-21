import os
import csv
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = input("Please enter your Supabase DATABASE_URL (e.g. postgresql://postgres:password@host...): ").strip()

print(f"Connecting to database...")

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Successfully connected. Reading CSV data...")

    raw_path = os.path.join(os.path.dirname(__file__), 'ml', 'data', 'raw', 'events_raw.csv')
    
    events_params = []
    
    with open(raw_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if count >= 500:
                break
                
            try:
                lat = float(row.get('latitude', 0))
                lon = float(row.get('longitude', 0))
                if lat == 0 or lon == 0:
                    continue
                
                # Check if event with external_id already exists to prevent duplicates
                ext_id = row.get('id')
                
                # Raw SQL params
                params = {
                    "id": str(uuid.uuid4()),
                    "external_id": ext_id,
                    "event_type": row.get('event_type', 'unplanned'),
                    "latitude": lat,
                    "longitude": lon,
                    "address": row.get('address', ''),
                    "event_cause": row.get('event_cause', 'others').lower(),
                    "requires_road_closure": row.get('requires_road_closure', 'FALSE').upper() == 'TRUE',
                    "start_datetime": row.get('start_datetime', datetime.now().isoformat()),
                    "end_datetime": row.get('end_datetime') if row.get('end_datetime', 'NULL') != 'NULL' else None,
                    "status": row.get('status', 'active'),
                    "priority": row.get('priority', 'Low'),
                    "corridor": row.get('corridor', 'Non-corridor'),
                    "zone": row.get('zone', '') if row.get('zone', 'NULL') != 'NULL' else None,
                    "junction": row.get('junction', '') if row.get('junction', 'NULL') != 'NULL' else None,
                    "police_station": row.get('police_station', '') if row.get('police_station', 'NULL') != 'NULL' else None,
                    "description": row.get('description', '') if row.get('description', 'NULL') != 'NULL' else None,
                    "veh_type": row.get('veh_type', '') if row.get('veh_type', 'NULL') != 'NULL' else None
                }
                events_params.append(params)
                count += 1
            except Exception as e:
                print(f"Error on row: {e}")
                continue

    if events_params:
        print(f"Adding {len(events_params)} events to the Supabase database...")
        
        # Using raw SQL to avoid any SQLAlchemy relationship/model errors
        insert_query = text("""
            INSERT INTO events (
                id, external_id, event_type, latitude, longitude, address, event_cause,
                requires_road_closure, start_datetime, end_datetime, status, priority,
                corridor, zone, junction, police_station, description, veh_type
            ) VALUES (
                :id, :external_id, :event_type, :latitude, :longitude, :address, :event_cause,
                :requires_road_closure, :start_datetime, :end_datetime, :status, :priority,
                :corridor, :zone, :junction, :police_station, :description, :veh_type
            ) ON CONFLICT (external_id) DO NOTHING
        """)
        
        session.execute(insert_query, events_params)
        session.commit()
        print("Successfully seeded the database! Your Supabase events table is now populated.")
    else:
        print("No new events to add. The database might already be populated.")
        
except Exception as e:
    print(f"Failed to seed database: {e}")
