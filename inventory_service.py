# inventory_service.py ────────────────────────────────────────────────────────
# WHY gRPC HERE?
#   The GUI needs to know IMMEDIATELY if a book is in stock before ordering.
#   gRPC is synchronous — client calls, server answers, client gets reply.
#   It's like a direct phone call between services: fast and typed.
#
# Run:  python inventory_service.py
# ──────────────────────────────────────────────────────────────────────────────

import grpc                          # gRPC framework
import book_pb2                      # StockRequest, StockResponse dataclasses
import book_pb2_grpc                 # InventoryServicer base + registration fn
from concurrent import futures       # gRPC needs a thread pool to handle requests

# ── In-memory inventory ───────────────────────────────────────────────────────
# Plain dict: book title → stock count. No database needed for this demo.
STOCK = {
    "The Pragmatic Programmer":               5,
    "Clean Code":                             3,
    "Designing Data-Intensive Applications":  2,
    "The Hobbit":                             8,
}

# ── Service implementation ────────────────────────────────────────────────────

class InventoryService(book_pb2_grpc.InventoryServicer):  # subclass the base
    """Real implementation: look up the book and return stock count."""

    def CheckStock(self, request, context):        # gRPC calls this for each request
        print(f"[gRPC] CheckStock ← '{request.title}'")   # log incoming call
        amount = STOCK.get(request.title, 0)       # 0 if book not found
        print(f"[gRPC] CheckStock → {amount} in stock")   # log outgoing reply
        return book_pb2.StockResponse(             # return a StockResponse object
            title=request.title,                   # echo the title back
            amount=amount,                         # stock count
        )

# ── Start the server ──────────────────────────────────────────────────────────

def serve():
    server = grpc.server(                          # create a gRPC server
        futures.ThreadPoolExecutor(max_workers=4)  # 4 threads handle concurrent requests
    )
    book_pb2_grpc.add_InventoryServicer_to_server( # register our service
        InventoryService(), server
    )
    server.add_insecure_port("[::]:50051")         # listen on port 50051, no TLS
    server.start()                                 # start accepting connections
    print("[gRPC] Inventory service running on port 50051 ...")
    server.wait_for_termination()                  # block until Ctrl+C

if __name__ == "__main__":
    serve()
