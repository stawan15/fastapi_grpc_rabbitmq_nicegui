# gui_client.py ───────────────────────────────────────────────────────────────
# The customer-facing GUI. Does two things:
#   1. CHECK STOCK → calls gRPC  (synchronous, needs immediate answer)
#   2. PLACE ORDER → publishes to RabbitMQ  (async, fire-and-forget)
#
# Run:  python gui_client.py
# Open: http://localhost:8080
# ──────────────────────────────────────────────────────────────────────────────

from nicegui import ui           # pip install nicegui
import grpc                      # pip install grpcio
import pika                      # pip install pika
import book_pb2                  # our message classes (shared, one copy)
import book_pb2_grpc             # our client stub (shared, one copy)

BOOKS = [                        # list of books the customer can pick from
    "The Pragmatic Programmer",
    "Clean Code",
    "Designing Data-Intensive Applications",
    "The Hobbit",
]

QUEUE_NAME = "book_orders"       # must match the queue name in order_worker.py

# ── gRPC helper ───────────────────────────────────────────────────────────────

def check_stock(title: str) -> str:
    """Open a gRPC channel, call CheckStock, return a result string."""
    with grpc.insecure_channel("localhost:50051") as channel:  # connect to inventory service
        stub = book_pb2_grpc.InventoryStub(channel)            # create client stub
        request = book_pb2.StockRequest(title=title)           # build the request message
        response = stub.CheckStock(request)                    # BLOCKING call — waits for reply
    return f"'{response.title}' — {response.amount} in stock"  # format result for display

# ── RabbitMQ helper ───────────────────────────────────────────────────────────

def place_order(title: str, qty: int) -> str:
    """Publish an order message to RabbitMQ and disconnect immediately."""
    conn = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")  # connect to local RabbitMQ
    )
    ch = conn.channel()                              # open channel
    ch.queue_declare(queue=QUEUE_NAME, durable=False) # ensure queue exists

    message = f"{title}|{qty}"                       # encode order as "title|qty"

    # Publish to the DEFAULT exchange (empty string "").
    # Default exchange routes by routing_key = queue name directly.
    # This is the simplest possible RabbitMQ setup — no exchange config needed.
    ch.basic_publish(
        exchange="",           # "" = RabbitMQ default exchange
        routing_key=QUEUE_NAME,# default exchange routes to queue with this exact name
        body=message.encode(), # message body as bytes
    )
    conn.close()               # close connection — we're done (fire and forget)
    return f"✅ Order placed: {qty}x '{title}' → sent to queue"

# ── NiceGUI Layout ────────────────────────────────────────────────────────────

with ui.card().classes("mx-auto mt-10 p-6 w-96"):    # centered card

    ui.label("📚 Book Order System").classes("text-2xl font-bold mb-4")

    # Book selection dropdown
    book_select = ui.select(
        options=BOOKS,                               # the books to choose from
        label="Select a Book",
        value=BOOKS[0],                              # default selection
    ).classes("w-full")

    # Quantity input
    qty_input = ui.number(
        label="Quantity",
        value=1,                                     # default quantity
        min=1, max=99,
    ).classes("w-full mt-2")

    # Result display area
    result_label = ui.label("").classes("mt-4 text-blue-600 font-medium")

    ui.separator()  # horizontal line

    # ── Check Stock button (uses gRPC) ────────────────────────────────────────
    def on_check():
        result_label.set_text("Checking stock via gRPC...")   # show loading state
        try:
            result = check_stock(book_select.value)           # synchronous gRPC call
            result_label.set_text(f"📊 {result}")
        except Exception as e:
            result_label.set_text(f"❌ gRPC error: {e}")      # show error if server is down

    ui.button("🔍 Check Stock (gRPC)", on_click=on_check).classes(
        "w-full mt-2 bg-blue-500 text-white"
    )

    # ── Place Order button (uses RabbitMQ) ────────────────────────────────────
    def on_order():
        try:
            result = place_order(book_select.value, int(qty_input.value))  # publish to queue
            result_label.set_text(result)
        except Exception as e:
            result_label.set_text(f"❌ RabbitMQ error: {e}")  # show error if broker is down

    ui.button("🛒 Place Order (RabbitMQ)", on_click=on_order).classes(
        "w-full mt-2 bg-green-500 text-white"
    )

ui.run(port=8080, title="Book Order System")   # start the web server on port 8080
