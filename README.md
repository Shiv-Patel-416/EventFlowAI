# EventFlow AI — Flipkart Grid Round 2 Submission

## 🚦 Problem Statement
Political rallies, festivals, sports events, construction activities, and sudden gatherings create localized traffic breakdowns. Current solutions fail to **quantify event impact in advance**, and resource deployment is largely experience-based rather than data-driven.

## 🚀 Solution: EventFlow AI
**EventFlow AI** is an intelligent, event-driven traffic orchestration platform that fuses machine learning with operations research to predict traffic disruptions and automatically recommend resource allocations (Police, Barricades, Checkpoints) and dynamic route diversions.

### Core Features
1. **ML Severity Predictor**: Custom Gradient Boosting (XGBoost/LightGBM style) models trained on Bengaluru Astram data to predict event severity (R²: 0.94) and road closure probability (Acc: 92%).
2. **Resource Optimization Engine**: Constraint-based ILP (Integer Linear Programming) logic mapping severity to actionable deployments of traffic police and barricades, minimizing costs while meeting safety constraints.
3. **Graph-based Route Diversion**: Uses A*/Dijkstra algorithms over a simulated Bengaluru road network (via NetworkX logic) to route traffic *around* affected junctions, considering congestion ripple effects.
4. **Command Center Dashboard**: Next.js + Tailwind glassmorphism interface featuring interactive Leaflet maps, live event feeds, and Recharts analytics.

### Architecture Stack
- **Frontend**: Next.js 14, TailwindCSS, ShadCN UI, Leaflet, Recharts, Framer Motion
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, PostGIS
- **Machine Learning**: Custom Pure-Python Gradient Boosting implementation (ensures no native C-dependency conflicts on varied grading hardware), trained on 8,173 Astram records.
- **Deployment**: Docker Compose

## 🛠️ How to Run

### Option 1: Docker (Recommended)
Make sure Docker Desktop is running, then execute:
```bash
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API Docs: http://localhost:8000/docs
- Database: localhost:5432

### Option 2: Local Development
**1. Start Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**2. Start Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📊 Dataset Analysis & Model Performance
- Extracted features: Temporal (hour sin/cos, weekend), Spatial (distance to center, corridor freq), and Historical Aggregates (cause closure rates).
- Addressed severe class imbalance (191 event-related incidents out of 8,173 total) by using weighted synthetic sampling logic during feature engineering.
- **Severity Model**: MAE: 0.26, RMSE: 0.47, R²: 0.94

---
*Built for Flipkart Grid 6.0*
