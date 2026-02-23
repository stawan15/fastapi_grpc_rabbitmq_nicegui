# order_worker.py ─────────────────────────────────────────────────────────────
# WHY RabbitMQ HERE?
#   When a customer places an order, we DON'T need an instant reply — we just
#   want the order processed in the background. RabbitMQ queues the work and
#   distributes it across however many workers are running (round-robin).
#   If workers are busy or crash, orders wait safely in the queue.
#
# Run MULTIPLE copies to see round-robin:
#   terminal 1:  python order_worker.py   (Worker A)
#   terminal 2:  python order_worker.py   (Worker B)
#   terminal 3:  python order_worker.py   (Worker C)
# Each order goes to the next worker in rotation.
#
# Requires RabbitMQ running locally:  docker run -d -p 5672:5672 rabbitmq
# ──────────────────────────────────────────────────────────────────────────────

import pika      # pip install pika  — pure-Python RabbitMQ client
import time      # to simulate processing delay
import os        # to get worker identity from environment (optional)

QUEUE_NAME = "book_orders"  # the queue name — must match what the publisher uses

# Give each worker a name so we can see who picks up which order
WORKER_NAME = os.environ.get("WORKER_NAME", f"Worker-{os.getpid()}")  # default: pid

def process_order(ch, method, properties, body):
    """
    This function is called by pika each time a message arrives.
    ch         = the channel (used to ack the message when done)
    method     = delivery metadata (routing key, delivery tag)
    properties = message headers (not used here)
    body       = raw bytes of the message
    """
    order = body.decode()                          # decode bytes → string "Title|Qty"
    parts = order.split("|")                       # split on pipe
    title = parts[0]                               # first part: book title
    qty   = parts[1] if len(parts) > 1 else "1"   # second part: quantity

    print(f"\n[{WORKER_NAME}] 📦 Received order: {qty}x '{title}'")
    time.sleep(1)                                  # simulate order processing work
    print(f"[{WORKER_NAME}] ✅ Order processed!")

    ch.basic_ack(delivery_tag=method.delivery_tag) # tell RabbitMQ "I'm done, remove msg"

def main():
    # Connect to RabbitMQ on localhost with default credentials (guest/guest)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")  # RabbitMQ host
    )
    channel = connection.channel()                   # open a channel (logical connection)

    # Declare the queue — safe to call multiple times, only creates if not exists
    # durable=False → queue disappears if RabbitMQ restarts (fine for demo)
    channel.queue_declare(queue=QUEUE_NAME, durable=False)

    # prefetch_count=1 → CRITICAL for round-robin fairness!
    # Without this, RabbitMQ dumps ALL messages on the first worker.
    # With this, a worker only gets the next message after finishing the current one.
    channel.basic_qos(prefetch_count=1)

    # Register our callback — pika calls process_order() for each message
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=process_order,  # our handler function above
        auto_ack=False,                     # we manually ack so no message is lost
    )

    print(f"[{WORKER_NAME}] 🟢 Waiting for orders on queue '{QUEUE_NAME}'...")
    print(f"[{WORKER_NAME}]    Press Ctrl+C to stop.\n")
    channel.start_consuming()              # block here, processing messages as they arrive

if __name__ == "__main__":
    main()
