# Modern Parking System

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

## Fee structure

| Duration | Fee |
|---|---|
| Up to 30 minutes | Free |
| 31 minutes – 2 hours | Ksh 50 |
| Over 2 – 4 hours | Ksh 100 |
| Over 4 – 6 hours | Ksh 300 |
| Over 6 hours | Ksh 500 |

## Project structure

```
parkingsystem.html    Frontend — self-contained HTML/CSS/JS (runs standalone via localStorage)
app.py                Backend API — Python/Flask
db.py                 MySQL connection handler
Database.sql          Database schema + seed data (40 slots, tariff bands)
Algorithm.docx        Pseudocode for all 7 modules
Data_structure.md     Data structures used and why (arrays, hash maps, queue, linked list, stack)
```

## Tech stack

- **Frontend:** HTML, CSS, vanilla JavaScript (no frameworks)
- **Backend:** Python, Flask, PyMySQL
- **Database:** MySQL

## Getting started

### Try the frontend alone (no setup needed)
Open `parkingsystem.html` directly in a browser. It runs entirely on
`localStorage`, so you can try every feature — entry, exit, payment,
admin dashboard — without a database or server.

### Run the full stack
```bash
# 1. Create the database
mysql -u root -p -e "CREATE DATABASE parking_system"
mysql -u root -p parking_system < Database.sql

# 2. Set up the backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install flask pymysql python-dotenv

# 3. Create a .env file in the project root:
#    DB_HOST=localhost
#    DB_USER=root
#    DB_PASSWORD=yourpassword
#    DB_NAME=parking_system
#    PORT=3000

# 4. Run the server
python app.py
```
The API is then available at `http://localhost:3000`.

## API reference

| Module | Endpoint | Description |
|---|---|---|
| 1 | `GET /api/slots` | All slots, plus count of free ones |
| 2/3 | `POST /api/entry` | Record entry — allocates a slot or queues if full |
| 4 | `GET /api/tickets/active/<plate>` | Live duration and fee for a parked vehicle |
| 5/6 | `POST /api/exit/<ticket_id>/pay` | Collect payment and open the barrier |
| 7 | `GET /api/admin/summary` | Revenue, vehicle count, and occupancy for a given date |

## Known limitations

- M-Pesa payment is simulated — not yet connected to Safaricom's Daraja API
- No authentication is implemented yet, though the schema includes a `users` table with roles for it
- The frontend and backend run independently (the frontend does not currently call the backend API)

