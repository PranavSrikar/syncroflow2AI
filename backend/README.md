# SYNCHROFLOW AI — Authoritative Python Backend

Authoritative Intelligent Adaptive Traffic Signal Control Backend for SYNCHROFLOW AI.

Developed in strict alignment with the master specification and wire protocol `v1.2.0`.

---

## 1. Architecture Overview (Phase A: FastAPI Foundation)

- **FastAPI Core**: Modular REST routes under `/api/v1` for health, simulation lifecycle, scenarios, controllers, emergencies, incidents, benchmarks, and system configuration.
- **Real-Time WebSocket Stream**: Bi-directional event stream on `/api/v1/ws/traffic` broadcasting authoritative simulation state at 10Hz, with sequence numbering, timestamps, and command acknowledgments.
- **Deterministic Simulation Service**: Authoritative state engine with Mulberry32 seeded PRNG, physical vehicle kinematics, and event-driven trip completion telemetry.
- **Safety Supervisor Interlocks**:
  - Independent safety rule enforcement rejecting conflicting simultaneous green movements across North-South and East-West corridors.
  - Clearance transitions: `GREEN` $\rightarrow$ `YELLOW_CLEARANCE` (3.5s standard, 4.5s monsoon) $\rightarrow$ `ALL_RED_CLEARANCE` (2.0s) $\rightarrow$ `GREEN`.
  - Emergency vehicle preemption with safe clearance guarantees.
- **Scenario Catalog**: Native support for all 25 canonical scenarios defined in the frontend.
- **Benchmark Runner**: Reproducible comparative evaluation engine across all 7 canonical controllers.

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── benchmarks.py
│   │   │   ├── configuration.py
│   │   │   ├── controllers.py
│   │   │   ├── emergencies.py
│   │   │   ├── health.py
│   │   │   ├── incidents.py
│   │   │   ├── scenarios.py
│   │   │   └── simulation.py
│   │   └── websocket.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── schemas/
│   │   ├── benchmarks.py
│   │   ├── commands.py
│   │   ├── simulation.py
│   │   ├── telemetry.py
│   │   └── traffic.py
│   ├── services/
│   │   └── simulation_service.py
│   └── main.py
├── tests/
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   └── test_websocket.py
│   └── unit/
│       ├── test_contracts.py
│       └── test_simulation_service.py
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 3. Local Installation & Startup

### Step 1: Create Virtual Environment
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Start the Backend Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Verify API & Documentation
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`
- WebSocket stream: `ws://localhost:8000/api/v1/ws/traffic`

### Step 5: Run Automated Tests
```bash
pytest
```

---

## 4. Frontend Integration

In the React frontend (`src/components/views/ConfigApiView.tsx`):
1. Switch provider mode from `Local Browser Engine (Demo Mode)` to `Authoritative Python Backend (FastAPI / SUMO)`.
2. Connect to `http://localhost:8000/api/v1` and `ws://localhost:8000/api/v1/ws/traffic`.
3. The frontend will immediately receive real-time authoritative 10Hz simulation state updates and dispatch control commands with structured sequence validation.
