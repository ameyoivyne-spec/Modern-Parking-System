CREATE TABLE vehicles (
    vehicle_id INT PRIMARY KEY AUTO_INCREMENT,
    plate_number VARCHAR(15) NOT NULL UNIQUE,
    vehicle_type VARCHAR(20),
    phone_number VARCHAR(15)
);

CREATE TABLE parking_slots (
    slot_id INT PRIMARY KEY AUTO_INCREMENT,
    slot_no VARCHAR(3) NOT NULL UNIQUE,
    slot_zone VARCHAR(1),
    slot_status ENUM('FREE', 'OCCUPIED', 'RESERVED', 'MAINTENANCE') DEFAULT 'FREE'
);
CREATE INDEX idx_slot_status ON parking_slots (slot_status);

CREATE TABLE tickets (
    ticket_id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_id INT NOT NULL,
    slot_id INT NOT NULL,
    entry_time TIMESTAMP NOT NULL DEFAULT NOW(),
    exit_time TIMESTAMP NULL,
    tickets_status ENUM('ACTIVE', 'CLOSED') DEFAULT 'ACTIVE',
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id)
);
CREATE INDEX idx_tickets_status ON tickets (tickets_status);
CREATE INDEX idx_tickets_entry ON tickets (entry_time);

CREATE TABLE tariff (
    tariff_band_id INT PRIMARY KEY AUTO_INCREMENT,
    min_minutes INT NOT NULL,
    max_minutes INT NOT NULL,
    fee DECIMAL(10,2) NOT NULL CHECK (fee>=0),
    description VARCHAR(100) NOT NULL,
    CONSTRAINT validity CHECK (min_minutes < max_minutes)
);

CREATE TABLE payments (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    ticket_id INT NOT NULL,
    tariff_band_id INT NOT NULL,
    duration INT NOT NULL,
    amount_due DECIMAL(10,2) NOT NULL,
    amount_paid DECIMAL(10,2) NOT NULL,
    method ENUM('CASH', 'MPESA'),
    payment_time TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id),
    FOREIGN KEY (tariff_band_id) REFERENCES tariff(tariff_band_id),
    CONSTRAINT sufficient CHECK (amount_paid >= amount_due)
);
CREATE INDEX idx_payments_time ON payments (payment_time);

CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(30) NOT NULL,
    user_password VARCHAR(255) NOT NULL COMMENT 'bcrypt/argon2 hash, never plaintext',
    user_role ENUM ('ADMIN', 'ATTENDANT')
);

CREATE TABLE audit_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_action VARCHAR(100) NOT NULL,
    username VARCHAR(30) NOT NULL,
    log_time TIMESTAMP  DEFAULT NOW()
);
CREATE INDEX idx_audit_time ON audit_log (log_time);

CREATE TABLE waiting_queue (
    queue_id INT PRIMARY KEY AUTO_INCREMENT,
    plate_number VARCHAR(15) NOT NULL,
    vehicle_type VARCHAR(20),
    phone_number VARCHAR(15),
    queued_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_queue_order ON waiting_queue (queued_at);

INSERT INTO tariff (min_minutes, max_minutes, fee, description) VALUES
(0, 30, 0.00, 'Up to 30 minutes (FREE)'),
(31, 120, 50.00, '31 minutes to 2 hours'),
(121, 240, 100.00, 'Over 2 hours to 4 hours'),
(241, 360, 300.00, 'Over 4 hours to 6 hours'),
(361, 99999, 500.00, 'Over 6 hours');

INSERT INTO parking_slots (slot_no, slot_zone) VALUES
('A1', 'A'), ('A2', 'A'), ('A3', 'A'), ('A4', 'A'), ('A5', 'A'), ('A6', 'A'), ('A7', 'A'), ('A8', 'A'), ('A9', 'A'), ('A10', 'A'),
('B1', 'B'), ('B2', 'B'), ('B3', 'B'), ('B4', 'B'), ('B5', 'B'), ('B6', 'B'), ('B7', 'B'), ('B8', 'B'), ('B9', 'B'), ('B10', 'B'),
('C1', 'C'), ('C2', 'C'), ('C3', 'C'), ('C4', 'C'), ('C5', 'C'), ('C6', 'C'), ('C7', 'C'), ('C8', 'C'), ('C9', 'C'), ('C10', 'C'),
('D1', 'D'), ('D2', 'D'), ('D3', 'D'), ('D4', 'D'), ('D5', 'D'), ('D6', 'D'), ('D7', 'D'), ('D8', 'D'), ('D9', 'D'), ('D10', 'D');

CREATE VIEW currently_parked AS
SELECT v.plate_number, t.ticket_id, t.slot_id, t.entry_time
FROM tickets t JOIN vehicles v ON v.vehicle_id = t.vehicle_id
WHERE t.tickets_status = 'ACTIVE';