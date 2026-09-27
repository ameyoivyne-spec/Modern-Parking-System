import os
from datetime import datetime, date as date_cls

from flask import Flask, request, jsonify
from dotenv import load_dotenv

from db import get_connection

load_dotenv()
app = Flask(__name__)

def audit(cur, action, username="system"):
    cur.execute(
        "INSERT INTO audit_log (user_action, username) VALUES (%s, %s)",
        (action, username),
    )

def fee_for_duration(cur, minutes):
    cur.execute(
        "SELECT * FROM tariff WHERE %s BETWEEN min_minutes AND max_minutes LIMIT 1",
        (minutes, minutes),
    )
    band = cur.fetchone()
    if band:
        return band
    cur.execute("SELECT * FROM tariff ORDER BY max_minutes DESC LIMIT 1")
    return cur.fetchone()

# Module 1: Slot Availability Display
@app.get("/api/slots")
def get_slots():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT slot_no, slot_zone, slot_status FROM parking_slots ORDER BY slot_no")
            slots = cur.fetchall()
        available = sum(1 for slot in slots if slot["slot_status"] == "FREE")
        return jsonify({"available": available,"total": len(slots), "slots": slots})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
# Module 2 + 3: Vehicle Entry + Slot Allocation
@app.post("/api/entry")
def vehicle_entry():
    data = request.get_json(silent=True) or {}
    plate_number = data.get("plate_number")
    if not plate_number:
        return jsonify({"error": "Plate number is required"}), 400
    plate = plate_number.strip().upper()
    vehicle_type = data.get("vehicle_type")
    phone_number = data.get("phone_number")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Check if the vehicle already exists
            cur.execute("SELECT t.ticket_id FROM tickets t JOIN vehicles v ON v.vehicle_id = t.vehicle_id WHERE v.plate_number = %s AND t.tickets_status = 'ACTIVE'", (plate,),)
            if cur.fetchone():
                conn.rollback()
                return jsonify({"error": "Vehicle is already parked"}), 409

            # Find an available slot
            cur.execute("SELECT * FROM parking_slots WHERE slot_status = 'FREE' ORDER BY slot_no LIMIT 1 FOR UPDATE")
            slot = cur.fetchone()
            if not slot:
                cur.execute("INSERT INTO waiting_queue (plate_number, vehicle_type, phone_number) VALUES (%s, %s, %s)", (plate, vehicle_type, phone_number),)
                cur.execute("SELECT COUNT(*) AS position FROM waiting_queue WHERE queued_at <= (SELECT queued_at FROM waiting_queue WHERE plate_number = %s ORDER BY queued_at DESC LIMIT 1)", (plate,),)
                position = cur.fetchone()["position"]
                conn.commit()
                return jsonify({"queued": True, "position": position, "message": "Parking full - added to waiting queue"}), 200

            #Upsert the vehicle, open a ticket, occupy the slot.
            cur.execute("INSERT INTO vehicles (plate_number, vehicle_type, phone_number) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE vehicle_type = VALUES(vehicle_type), phone_number = VALUES(phone_number)", (plate, vehicle_type, phone_number),)
            cur.execute("SELECT vehicle_id FROM vehicles WHERE plate_number = %s", (plate,))
            vehicle_id = cur.fetchone()["vehicle_id"]

            cur.execute("INSERT INTO tickets (vehicle_id, slot_id, entry_time, tickets_status) VALUES (%s, %s, NOW(), 'ACTIVE')", (vehicle_id, slot["slot_id"]),)
            ticket_id = cur.lastrowid

            cur.execute("UPDATE parking_slots SET slot_status = 'OCCUPIED' WHERE slot_id = %s", (slot["slot_id"],))
            audit(cur, f"Vehicle {plate} entered and allocated to slot {slot['slot_no']}")
            conn.commit()

            return jsonify({"ticket_id": ticket_id, "plate": plate, "slot_no": slot["slot_no"], "slot_zone": slot["slot_zone"], "entry_time": datetime.now().isoformat(),}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Module 4: Duration and fee calculation
@app.get("/api/tickets/active/<plate>")
def active_ticket(plate):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT t.ticket_id, t.slot_id, t.entry_time, ps.slot_no, ps.slot_zone, TIMESTAMPDIFF(MINUTE, t.entry_time, NOW()) AS duration_minutes FROM tickets t JOIN vehicles v ON v.vehicle_id = t.vehicle_id JOIN parking_slots ps ON ps.slot_id = t.slot_id WHERE v.plate_number = %s AND t.tickets_status = 'ACTIVE'", (plate.strip().upper(),),)
            ticket = cur.fetchone()
            if not ticket:
                return jsonify({"error": "Vehicle not found or has no active ticket"}), 404
            band = fee_for_duration(cur, ticket["duration_minutes"])
        return jsonify({ **ticket, "fee": float(band["fee"]), "tariff_band_id": band["tariff_band_id"], "description": band["description"],})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Module 5 + 6: Payment collection + Exit barrier control
@app.post("/api/exit/<int:ticket_id>/pay")
def pay_and_exit(ticket_id):
    data = request.get_json(silent=True) or {}
    Cash_input = data.get("amount_paid")
    method = data.get("method")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tickets WHERE ticket_id = %s AND tickets_status = 'ACTIVE' FOR UPDATE", (ticket_id,),)
            ticket = cur.fetchone()
            if not ticket:
                conn.rollback()
                return jsonify({"error": "Ticket not found or already closed"}), 404
            minutes = max(0, round((datetime.now() - ticket["entry_time"]).total_seconds() / 60))
            band = fee_for_duration(cur, minutes)
            fee = float(band["fee"])
            amount_paid, used_method = 0.0, None

            if fee == 0:
                pass
            elif method == "MPESA":
                amount_paid = fee
                used_method = "MPESA"
            elif method == "CASH":
                cash = float(cash_input or 0)
                if cash < fee:
                    conn.rollback()
                    return jsonify({"error": "Insufficient cash payment", "amount_due": fee}), 400
                amount_paid = cash
                used_method = "CASH"
            else:
                conn.rollback()
                return jsonify({"error": "Invalid payment method"}), 400
           
            cur.execute("INSERT INTO payments (ticket_id, tariff_band_id, duration, fee, amount_paid, used_method, payment_time) VALUES (%s, %s, %s, %s, %s, %s, NOW())", (ticket_id, band["tariff_band_id"], minutes, amount_due, amount_paid, method),)
            # Update ticket and slot status to reflect payment and exit
            cur.execute("UPDATE tickets SET tickets_status = 'CLOSED', exit_time = NOW() WHERE ticket_id = %s", (ticket_id,))
            cur.execute("UPDATE parking_slots SET slot_status = 'FREE' WHERE slot_id = %s", (ticket["slot_id"],))

            # Hand the freed slot to the next driver in the waiting queue, if any.
            cur.execute("SELECT * FROM waiting_queue ORDER BY queued_at LIMIT 1")
            next_in_queue = cur.fetchone()
            notified = None
            if next_in_queue:
                cur.execute("DELETE FROM waiting_queue WHERE queue_id = %s", (next_in_queue["queue_id"],))
                notified = next_in_queue["plate_number"]

            audit(cur, f"Exit processed for ticket {ticket_id}, fee Ksh {fee} via {used_method or 'FREE_EXIT'}")
            conn.commit()

            return jsonify({"status": "CONFIRMED", "barrier": "OPEN", "duration_minutes": minutes, "fee": fee, "amount_paid": amount_paid, "change": amount_paid - fee, "notified_next": notified, })
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Module 7: Admin and Reporting
@app.get("/api/admin/summary")
def admin_summary():
    conn = get_connection()
    try:
        report_date = request.args.get("date") or date_cls.today().isoformat()
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(method, 'FREE') AS method, SUM(amount_paid) AS revenue FROM payments WHERE DATE(payment_time) = %s GROUP BY method", (report_date,),)
            revenue  = cur.fetchall()

            cur.execute("SELECT COUNT(*) AS c FROM tickets WHERE DATE(entry_time) = %s", (report_date,))
            vehicles_summary = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM parking_slots WHERE slot_status = 'OCCUPIED'")
            occupied = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM parking_slots")
            total = cur.fetchone()["c"]

        occupancy_rate = round(occupied / total * 100, 1) if total else 0
        return jsonify({
            "date": report_date,
            "revenue_by_method": revenue,
            "vehicles_summary": vehicles_summary,
            "occupancy_rate": occupancy_rate,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)