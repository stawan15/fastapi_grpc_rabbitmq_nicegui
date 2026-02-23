# 📚 Book Order System — Setup & Run Guide

## What's in each file?

| File | Role | Why this tech? |
|---|---|---|
| `book.proto` | gRPC contract (schema) | Defines the API between client & server |
| `book_pb2.py` | Proto message classes | **ONE copy** — shared by all services |
| `book_pb2_grpc.py` | gRPC stub + servicer | **ONE copy** — shared by all services |
| `inventory_service.py` | gRPC server | Sync stock check — client needs instant answer |
| `order_worker.py` | RabbitMQ consumer | Async order processing — run multiple copies! |
| `gui_client.py` | NiceGUI frontend | Customer interface at http://localhost:8080 |

---

## Install Dependencies

```bash
pip install grpcio grpcio-tools pika nicegui
```

---

## Start RabbitMQ (Docker is easiest)

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
```
RabbitMQ dashboard: http://localhost:15672 (guest/guest)

---

## Run Everything (4 terminals)

**Terminal 1 — gRPC Inventory Service:**
```bash
python inventory_service.py
# Output: [gRPC] Inventory service running on port 50051...
```

**Terminal 2 — Order Worker A:**
```bash
python order_worker.py
# Output: [Worker-XXXX] Waiting for orders...
```

**Terminal 3 — Order Worker B (round-robin partner!):**
```bash
python order_worker.py
# Output: [Worker-YYYY] Waiting for orders...
```

**Terminal 4 — GUI Client:**
```bash
python gui_client.py
# Open browser: http://localhost:8080
```

---

## See Round-Robin in Action

1. Open http://localhost:8080
2. Select a book, set quantity
3. Click **"Place Order"** multiple times
4. Watch Terminal 2 and Terminal 3 — orders alternate between workers!

```
Terminal 2: [Worker-1234] Received order: 2x 'Clean Code'
Terminal 3: [Worker-5678] Received order: 1x 'The Hobbit'
Terminal 2: [Worker-1234] Received order: 3x 'Clean Code'   ← alternates!
```

This works because `basic_qos(prefetch_count=1)` limits each worker to one
message at a time. RabbitMQ naturally distributes via the default exchange.

---

## Generate the real proto files (optional, replaces hand-written pb2 files)

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. book.proto
```

This overwrites `book_pb2.py` and `book_pb2_grpc.py` with the real generated
versions using binary protobuf encoding.

---

## Data Flow Summary

```
[NiceGUI GUI]
     │
     ├── "Check Stock" ──gRPC──► [inventory_service.py]  sync, instant reply
     │                               (in-memory STOCK dict)
     │
     └── "Place Order" ──pika──► [RabbitMQ default exchange]
                                          │
                                 ┌────────┴────────┐
                              [Worker A]       [Worker B]     ← round-robin!
```
This repository hosts a Book Order System designed to demonstrate a microservices-style architecture using Python. It showcases how to integrate synchronous and asynchronous communication patterns in a single application.

Key Technologies & Architecture:

Frontend: NiceGUI (gui_client.py) provides a web interface for customers to browse books and place orders.
Synchronous Communication: gRPC (inventory_service.py) is used for real-time inventory checks where the client needs an immediate response.
Asynchronous Communication: RabbitMQ (order_worker.py) handles order processing in the background. It demonstrates a round-robin distribution of tasks among multiple worker instances.
API Definition: Protobuf (book.proto) defines the contract for data exchange between the services.
