# Smart Parking

An automated parking management system built for the Kenyan market. Drivers
can see live slot availability before entry, vehicle entry and exit are
recorded automatically, parking fees are calculated from time spent, and
the exit barrier opens on confirmed M-Pesa or cash payment.

## Features

1. **Slot Availability Display** — live grid of free/occupied slots by zone
2. **Vehicle Entry** — records plate number, vehicle type, and phone number
3. **Slot Allocation** — automatically assigns the lowest available slot
4. **Duration & Fee Calculation** — computes parking fee from time parked
5. **Payment Collection** — M-Pesa (STK push) or cash, with change calculation
6. **Exit Barrier Control** — opens only once payment is confirmed
7. **Admin & Reporting** — daily revenue by payment method, vehicle counts, occupancy rate
   
### Nice touches
- Single-page frontend with tabs: **Slots · Entry · Exit & Payment · Admin**
- Live connection badge showing whether the backend is reachable
- Automatic handover: when a vehicle exits, the next driver in the waiting queue is notified
- Dark-mode support and mobile-friendly (responsive, safe-area aware) UI
- Database constraints and row locking (`FOR UPDATE`) keep slot allocation race-free
  
## Fee structure

| Duration | Fee |
|---|---|
| Up to 30 minutes | Free |
| 31 minutes – 2 hours | Ksh 50 |
| Over 2 – 4 hours | Ksh 100 |
| Over 4 – 6 hours | Ksh 300 |
| Over 6 hours | Ksh 500 |

## Project structure
`````
parkingsystem.html    Frontend — self-contained SPA (calls the API at http://127.0.0.1:3000)
app.py                Backend API — all 7 modules as Flask routes
db.py                 MySQL connection handler (reads DB config from .env)
Database.sql          Schema + seed data: 7 tables, 40 slots (zones A–D), 5 tariff bands
ALGORITHMS.docx       Pseudocode for all 7 modules
Data structure.md     Data structures used and why (arrays, hash maps, queue, etc.)
usecase.md             Actors, use case diagram and use case summary
`````
## Tech stack

- **Frontend:** HTML, CSS, vanilla JavaScript — one self-contained file, no frameworks or build step
- **Backend:** Python 3, Flask, Flask-CORS, PyMySQL, python-dotenv
- **Database:** MySQL (schema, seed data, indexes, constraints and a `currently_parked` view in `Database.sql`)

## Database overview

| Table | Purpose |
|---|---|
| `vehicles` | One row per unique plate number |
| `parking_slots` | 40 slots in zones A–D (`FREE`/`OCCUPIED`/`RESERVED`/`MAINTENANCE`) |
| `tickets` | Entry/exit record per parking session (`ACTIVE`/`CLOSED`) |
| `tariff` | Fee bands (min/max minutes → fee) |
| `payments` | Amount due/paid, method (`CASH`/`MPESA`); CHECK constraint: `amount_paid >= amount_due` |
| `waiting_queue` | FIFO queue of drivers waiting for a slot |
| `users` | `ADMIN`/`ATTENDANT` roles, ready for future authentication |
| `audit_log` | Timestamped record of every entry/exit action |
| `currently_parked` | View of all vehicles with an active ticket |
## Getting started

### Prerequisites
- Python 3.8+
- MySQL 8
- pip

### 1. Create and seed the database
    mysql -u root -p -e "CREATE DATABASE parking_system"
    mysql -u root -p parking_system < Database.sql

### 2. Configure and run the backend
    python -m venv venv
    source venv/bin/activate        # Windows: venv\Scripts\activate
    pip install flask flask-cors pymysql python-dotenv

Create a `.env` file in the project root:
    DB_HOST=localhost
    DB_PORT=3306
    DB_USER=root
    DB_PASSWORD=yourpassword
    DB_NAME=parking_system
    PORT=3000

Start the server:
    python app.py
The API is now available at `http://localhost:3000`.

### 3. Open the frontend
Open `parkingsystem.html` in any browser. It talks to the API at
`http://127.0.0.1:3000` (see `API_BASE` at the top of the script if you need to change
the address). The header badge will show **"Connected to backend"** once everything is up.

## API reference

| Module | Endpoint | Method | Description |
|---|---|---|---|
| 1 | `/api/slots` | GET | All slots plus `available`/`total` counts |
| 2/3 | `/api/entry` | POST | Record entry — allocates lowest free slot, or queues if full. Body: `{plate_number, vehicle_type, phone_number}` |
| 4 | `/api/tickets/active/<plate>` | GET | Live duration, tariff band and fee for a parked vehicle |
| 5/6 | `/api/exit/<ticket_id>/pay` | POST | Collect payment, close ticket, free slot, open barrier, notify next in queue. Body: `{method: "MPESA"}` or `{method: "CASH", amount_paid: n}` |
| 7 | `/api/admin/summary?date=YYYY-MM-DD` | GET | Revenue by method, vehicles entered, occupancy rate |
| 7 | `/api/admin/recent-exits` | GET | Last 8 closed tickets (plate, slot, exit time, fee) |

### Example: full entry → exit flow
    # Enter
    curl -X POST http://localhost:3000/api/entry \
      -H "Content-Type: application/json" \
      -d '{"plate_number":"KDA 123A","vehicle_type":"Car","phone_number":"0712345678"}'
    # → {"ticket_id": 12, "plate": "KDA 123A", "slot_no": "A1", "slot_zone": "A", ...}

    # Check what is owed
    curl http://localhost:3000/api/tickets/active/KDA%20123A
    # → {"duration_minutes": 95, "fee": 50.0, "description": "31 minutes to 2 hours", ...}

    # Pay with M-Pesa (simulated) and open the barrier
    curl -X POST http://localhost:3000/api/exit/12/pay \
      -H "Content-Type: application/json" \
      -d '{"method":"MPESA"}'
    # → {"status": "CONFIRMED", "barrier": "OPEN", "fee": 50.0, ...}

## Known limitations

- M-Pesa payment is simulated — not yet connected to Safaricom's Daraja API
- No authentication is implemented yet, though the schema includes a `users` table with roles for it
- Notifications are in-app only — no SMS to drivers in the waiting queue
- Tariff bands cover duration only (no overnight / monthly passes yet)

## License

MIT
