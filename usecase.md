## 1. Actors

| Actor | Description |
| --- | --- |
| **Driver** | A motorist who wants to park or leave. Interacts indirectly through the attendant or a display at the gate. |
| **Parking Attendant** | Operates the entry/exit terminals: records entries, looks up tickets, collects payments. Primary user of the frontend tabs *Entry* and *Exit & Payment*. |
| **Administrator** | Reviews daily revenue by payment method, vehicle counts, occupancy rate and recent exits via the *Admin* tab; audits actions through the `audit_log`. |
| **M-Pesa (Daraja API)** | *External, simulated.* Sends the STK push and the payment confirmation callback. |
| **System (Timer)** | Internal actor that computes elapsed parking duration at lookup/payment time. |

## 2. Use case diagram

```mermaid
flowchart LR
    Driver((Driver))
    Attendant((Parking Attendant))
    Admin((Administrator))
    Mpesa((M-Pesa / Daraja - simulated))

    subgraph System["Modern Parking System"]
        UC1[UC-01 View slot availability]
        UC2[UC-02 Record vehicle entry]
        UC3[UC-03 Allocate slot / join waiting queue]
        UC4[UC-04 View duration & fee]
        UC5[UC-05 Pay & exit]
        UC6[UC-06 Notify next queued driver]
        UC7[UC-07 View admin reports]
    end

    Driver --> UC1
    Attendant --> UC2
    Attendant --> UC4
    Attendant --> UC5
    Admin --> UC7
    UC2 -.include.-> UC3
    UC5 -.include.-> UC4
    UC5 -.extend.-> UC6
    UC5 --> Mpesa
```

## 3. Use case summary

| ID | Use case | Primary actor | Priority |
| --- | --- | --- | --- |
| UC-01 | View slot availability | Driver / Attendant | High |
| UC-02 | Record vehicle entry | Parking Attendant | High |
| UC-03 | Allocate slot (or join waiting queue) | System | High |
| UC-04 | View duration & fee | Parking Attendant | High |
| UC-05 | Pay & exit (M-Pesa / cash / free) | Parking Attendant + Driver | High |
| UC-06 | Notify next driver in waiting queue | System | Medium |
| UC-07 | View admin reports | Administrator | Medium |

---

