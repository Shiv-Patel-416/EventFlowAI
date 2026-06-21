import os
import csv
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# You can set the DATABASE_URL environment variable before running the script,
# or simply hardcode your Supabase connection string here temporarily.
# Example: postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = input("Please enter your Supabase DATABASE_URL (e.g. postgresql://postgres:password@host...): ").strip()

print(f"Connecting to database...")

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Import the Event model
    # We must add backend to path so we can import app
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    from app.models.event import Event

    print("Successfully connected. Reading CSV data...")

    raw_path = os.path.join(os.path.dirname(__file__), 'ml', 'data', 'raw', 'events_raw.csv')
    
    events_to_add = []
    
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
                existing = session.query(Event).filter(Event.external_id == ext_id).first()
                if existing:
                    continue
                    
                e = Event(
                    id=uuid.uuid4(),
                    external_id=ext_id,
                    event_type=row.get('event_type', 'unplanned'),
                    latitude=lat,
                    longitude=lon,
                    address=row.get('address', ''),
                    event_cause=row.get('event_cause', 'others').lower(),
                    requires_road_closure=row.get('requires_road_closure', 'FALSE').upper() == 'TRUE',
                    start_datetime=row.get('start_datetime', datetime.now().isoformat()),
                    end_datetime=row.get('end_datetime') if row.get('end_datetime', 'NULL') != 'NULL' else None,
                    status=row.get('status', 'active'),
                    priority=row.get('priority', 'Low'),
                    corridor=row.get('corridor', 'Non-corridor'),
                    zone=row.get('zone', '') if row.get('zone', 'NULL') != 'NULL' else None,
                    junction=row.get('junction', '') if row.get('junction', 'NULL') != 'NULL' else None,
                    police_station=row.get('police_station', '') if row.get('police_station', 'NULL') != 'NULL' else None,
                    description=row.get('description', '') if row.get('description', 'NULL') != 'NULL' else None,
                    veh_type=row.get('veh_type', '') if row.get('veh_type', 'NULL') != 'NULL' else None
                )
                events_to_add.append(e)
                count += 1
            except Exception as e:
                print(f"Error on row: {e}")
                continue

    if events_to_add:
        print(f"Adding {len(events_to_add)} events to the Supabase database...")
        session.bulk_save_objects(events_to_add)
        session.commit()
        print("Successfully seeded the database! Your Supabase events table is now populated.")
    else:
        print("No new events to add. The database might already be populated.")
        
except Exception as e:
    print(f"Failed to seed database: {e}")
