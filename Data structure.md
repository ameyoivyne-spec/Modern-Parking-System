# Data Structures and Justification

| Data Structure | Where Used | Justification |
|---|---|---|
| Array  | Parking slots (Module 1, 3) | Slots are fixed in number and identified by a slot number, so a plain array gives direct index access which is ideal for rendering the slot grid and scanning for the lowest free slot_no, with no insertions or shifting needed. |
| Array | Fee schedule loaded from tariff table (Module4) | The tariff table has a small, fixed number of bands. Loading it into an array at startup and scanning it linearly is fast enough at this size and unlike hard-coded IF/ELSE thresholds, lets an admin change fees by editing the tariff table with no code change. | 
| Hash Map | Active tickets that are looked up by ticket_id (Module 4, 6) | Exit processing must find a ticket's entry time and slot instantly. A hash map gives average O(1) lookup which matters directly for barrier speed. |
| Hash Map | Plate number through the active ticket ID (Module 2,4) | Drivers are identified by plate, not by ticket_id in an instant  mapping from plate to ticket |
| Queue  | Waiting drivers when parking is full (Module 2) | FIFO order is fair where first driver to arrive enters first when a slot frees |
| Linked List  | Archive of exited vehicles (Module 6, 7) | The archive grows without a known bound and new exits are always inserted at the front, so a linked list avoids the resize cost of growing array and keeps "most recent exits" reports O(1) to produce. |
| Stack | Undo of admin actions/ processing ticket print jobs (Module 7) | Last action is reserved for first(LIFO). The most recent admin action is the first one that should be undoable and the most recently queued print job should be handled next. | 
