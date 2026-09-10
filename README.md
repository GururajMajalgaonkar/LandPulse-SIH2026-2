
# LandPulse — SIH 2026 Prototype

A working full-stack prototype for:
**Real-Time National Land Acquisition & Management System for End-to-End Digital Monitoring and Decision Support**

## Features
- Role-based login: admin, collector, officer, farmer
- SQLite database with seeded demo data
- Government project creation
- Land parcel registration
- GIS map using Leaflet + OpenStreetMap
- End-to-end parcel lifecycle
- Risk and delay flags
- Compensation and payment tracking
- Farmer objection submission
- Document upload
- Decision-support dashboard
- Audit log backend
- REST endpoints for map and statistics

## Run locally

1. Install Python 3.10+
2. Open terminal in this folder.
3. Run:
   `python -m venv .venv`
4. Activate it:
   Windows:
   `.venv\Scripts\activate`
   macOS/Linux:
   `source .venv/bin/activate`
5. Install:
   `pip install -r requirements.txt`
6. Start:
   `python app.py`
7. Open:
   `http://127.0.0.1:5000`

## Demo credentials
Officer:
- revenue@sih.local
- admin123

Collector:
- collector@sih.local
- admin123

Farmer:
- farmer@sih.local
- farmer123

## Notes
This is an SIH demonstration prototype, not a production government deployment. For production, integrate authorized land-record APIs, state identity/e-sign systems, payment gateways, government notification services, stronger audit/security controls, backups, and official legal workflows.


## Enhanced Officer Portal
- Added a dedicated `/officer` Officer Portal.
- Officers can click GIS parcel markers to see owner name, area, compensation, payment status, project, risk and lifecycle status.
- Added a direct “View Details” action for every parcel.
- `/api/map` now returns the owner and compensation fields used by the GIS popup.


## Run locally
1. `python -m venv venv`
2. Windows: `venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `python app.py`
5. Open `http://localhost:5000`

Officer demo login: `revenue@sih.local` / `admin123`
Collector demo login: `collector@sih.local` / `admin123`
Farmer demo login: `farmer@sih.local` / `farmer123`

Officer/collector/admin accounts now go directly to the Officer Portal after login. The database is initialized automatically for both local and deployed starts.
