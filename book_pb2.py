# book_pb2.py ─────────────────────────────────────────────────────────────────
# Normally AUTO-GENERATED — run once:
#   pip install grpcio-tools
#   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. book.proto
#
# We ship this hand-written copy so you can read it clearly.
# ONE FILE — shared by inventory_service.py, gui_client.py. Never duplicate it.
# ──────────────────────────────────────────────────────────────────────────────

# protoc normally outputs a dense binary descriptor block here.
# For this demo we use simple Python dataclasses that behave identically
# for our purposes (attribute access, construction with keyword args).

from dataclasses import dataclass, field  # stdlib — no extra install needed

@dataclass
class StockRequest:
    """
    Maps to `message StockRequest` in book.proto.
    The client fills this and passes it to the stub.
    """
    title: str = ""          # proto field 1  →  the book title to look up

@dataclass
class StockResponse:
    """
    Maps to `message StockResponse` in book.proto.
    The server fills this and returns it to the client.
    """
    title:  str = ""         # proto field 1  →  book title (echoed back)
    amount: int = 0          # proto field 2  →  copies in stock
