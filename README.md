# EventFlow AI — Traffic Intelligence & Orchestration Platform

## 🎯 The Motive (Why does this exist?)
Political rallies, festivals, sports events, construction activities, and sudden VIP movements create localized traffic breakdowns. Current traffic management solutions are **reactive**—they only respond to congestion after it happens. 

**EventFlow AI** was built to be **proactive**. It is a full-stack intelligence platform that fuses machine learning with operations research to predict traffic disruptions *before* they peak. It automatically calculates how bad a jam will be, estimates how long it will last, and deploys the exact number of police and barricades needed to contain it.

---

## ✨ What Does This Website Do? (Key Features)

### 1. Command Center / Overview
The main dashboard ingests live traffic data and provides real-time tracking of active incidents. It displays high-level KPIs (Total Incidents, Critical Alerts, Average Resolution Time) to give city managers a bird's-eye view of the road network.

### 2. AI Predictor (Impact Simulation)
This is the core ML engine of the platform. You input the parameters of an upcoming event (e.g., a VIP movement at MG Road), and the AI calculates:
- **Severity Score (0-10)**
- **Probability of Road Closure**
- **Estimated Duration (Hours)**
- **Resource Deployment Plan** (Exact number of Police Units, Barricades, and Budget needed).

### 3. Route Diversion Engine
Using A*/Dijkstra algorithms over a simulated road network graph, the system calculates the fastest alternative routes around the incident, ensuring that diverted traffic doesn't cause a secondary "cascade" jam.

### 4. Jurisdiction Leaderboard
A gamified tracking system for Police Stations. It tracks how efficiently a specific station clears an incident compared to what the AI predicted.

---

## 🧮 How Are Things Calculated? (Is it hard-coded?)
**Nothing is hard-coded.** All metrics are dynamically generated using **XGBoost v3.0 Machine Learning models** trained on 8,173 real-world Bengaluru Astram traffic records.

### The Efficiency Score Explained
If you look at the Leaderboard, you will notice the Efficiency Score jumping or dropping dynamically. This is a live mathematical calculation:
> **Efficiency Score = (Actual Resolution Time) / (AI Baseline Predicted Time)**

- **Score < 1.0 (e.g., 0.82):** The police station cleared the incident *faster* than the AI expected. This is a **GOOD** score.
- **Score > 1.0 (e.g., 1.28):** The police station was *slower* than the AI baseline.
This introduces "Human-in-the-Loop" feedback, allowing the traffic department to track objective performance and budget resources to slower stations.

---

## ⚠️ The AI Simulator: "The Nuclear Option" Problem
When testing the **AI Predictor (Impact Simulation)**, you might notice that selecting two completely different locations (e.g., MG Road vs KR Puram Bridge) sometimes generates the **exact same Deployment Plan and Budget**. 

### The Logic Chain (Why this happens):
1. **You selected the "Nuclear Option":** If you select `VIP / VVIP Movement`, explicitly flag it as `Critical` Priority, and manually check the `Road Closure Required` box, you are creating a worst-case scenario.
2. **The ML Model Maxes Out:** In the XGBoost model we trained, a forced road closure for a critical VIP movement carries massive mathematical weight. These manual overrides completely overpower the subtle location-based features (like `distance_to_center_km`). The ML model instantly outputs a maximum **Severity of 10.0** and a **Duration of 4.5h** regardless of where it happens.
3. **The Deployment Engine calculates based on Impact, not Name:** The Resource Optimizer calculates Police units and Budget purely based on Severity and Duration. Since both locations resulted in 10.0 severity and 4.5h duration, the Deployment Engine allocates the exact same budget (e.g., 45 Police, ₹255,150) to handle it.

### How to handle this (Demonstrating Location Variance):
To see the ML model dynamically change the budget and severity based *purely* on the location, you need to give it a less extreme event. 
- Try selecting **"Vehicle Breakdown"** or **"Pothole Repair"**.
- Leave the priority on **"Standard"**.
- **UNCHECK** the Road Closure box. 

If you do this, the model will rely on the geographical features. You will see that a breakdown on a major bridge might cause a Severity of `6.5` with a high budget, while a breakdown on a small side street might only cause a Severity of `3.2` with a tiny budget!

---

## 🧪 How to Upload Custom Datasets (For Judges)
The application currently uses a production-ready PostgreSQL database hosted on **Supabase**. If you would like to test the live Vercel map by uploading your own CSV dataset of traffic incidents, you can easily do so using the built-in database seeder script.

1. Locate the file `ml/data/raw/events_raw.csv` in the project directory.
2. Replace its contents with your own dataset (ensure the column names match the existing format, such as `latitude`, `longitude`, `event_cause`, etc).
3. Run the seeder script from your terminal:
   ```bash
   python seed_supabase.py
   ```
4. When prompted, enter the Supabase Connection Pooler URL. 
5. The script uses a safe batch-uploader and `ON CONFLICT DO NOTHING` logic, so it will securely upload thousands of your custom rows directly to the cloud without crashing or duplicating data. Once the script finishes, simply refresh the live Vercel website to see your custom dots appear on the map!

---

## 💻 What is being used inside? (Tech Stack)
- **Frontend:** Next.js 14, TailwindCSS, Framer Motion, Leaflet.js
- **Backend:** FastAPI, Python, SQLAlchemy, PostgreSQL
- **Machine Learning:** XGBoost v3.0, Scikit-Learn, Imbalanced-Learn (SMOTE/Tomek Links)
- **Deployment:** Docker, Docker-Compose

---

## 🚀 How to Use / Run Locally

### Option 1: Docker (Recommended)
Make sure Docker Desktop is running, then execute:
```bash
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API Docs: http://localhost:8000/docs

### Option 2: Local Development
**1. Start Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
**2. Start Frontend:**
```bash
cd frontend
npm install
npm run dev
```
