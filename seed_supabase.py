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
    
    # Define the insert query here so it can be used inside the loop for batching
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
    
    with open(raw_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                lat = float(row.get('latitude', 0))
                lon = float(row.get('longitude', 0))
                if lat == 0 or lon == 0:
                    continue
                
                # Check if event with external_id already exists to prevent duplicates
                ext_id = row.get('id')
                
                start_dt = row.get('start_datetime', '').strip()
                if not start_dt or start_dt.upper() == 'NULL':
                    start_dt = datetime.now().isoformat()
                    
                end_dt = row.get('end_datetime', '').strip()
                if not end_dt or end_dt.upper() == 'NULL':
                    end_dt = None

                # Raw SQL params
                params = {
                    "id": str(uuid.uuid4()),
                    "external_id": ext_id,
                    "event_type": row.get('event_type', 'unplanned'),
                    "latitude": lat,
                    "longitude": lon,
                    "address": row.get('address', ''),
                    "event_cause": row.get('event_cause', 'others').lower(),
                    "requires_road_closure": str(row.get('requires_road_closure', '')).upper() == 'TRUE',
                    "start_datetime": start_dt,
                    "end_datetime": end_dt,
                    "status": row.get('status', 'active'),
                    "priority": row.get('priority', 'Low'),
                    "corridor": row.get('corridor', 'Non-corridor'),
                    "zone": row.get('zone', '') if row.get('zone', '').upper() != 'NULL' else None,
                    "junction": row.get('junction', '') if row.get('junction', '').upper() != 'NULL' else None,
                    "police_station": row.get('police_station', '') if row.get('police_station', '').upper() != 'NULL' else None,
                    "description": row.get('description', '') if row.get('description', '').upper() != 'NULL' else None,
                    "veh_type": row.get('veh_type', '') if row.get('veh_type', '').upper() != 'NULL' else None
                }
                events_params.append(params)
                count += 1
                
                # Batch insert every 1000 rows to prevent memory/timeout issues
                if len(events_params) >= 1000:
                    try:
                        session.execute(insert_query, events_params)
                        session.commit()
                        print(f"Inserted {count} rows...")
                    except Exception as batch_e:
                        session.rollback()
                        print(f"Batch failed, rolling back! Error: {batch_e}")
                    events_params = []

            except Exception as e:
                print(f"Error on row: {e}")
                continue

    if events_params:
        print(f"Adding {len(events_params)} events to the Supabase database...")
        
        print(f"Adding final {len(events_params)} events to the Supabase database...")
        try:
            session.execute(insert_query, events_params)
            session.commit()
            print("Successfully seeded the database! Your Supabase events table is now populated.")
        except Exception as final_e:
            session.rollback()
            print(f"Final batch failed: {final_e}")
    else:
        print("No new events to add. The database might already be populated.")
        
except Exception as e:
    print(f"Failed to seed database: {e}")
