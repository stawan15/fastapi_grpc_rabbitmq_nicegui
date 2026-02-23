# book_pb2_grpc.py ────────────────────────────────────────────────────────────
# Normally AUTO-GENERATED alongside book_pb2.py by protoc.
# ONE FILE — shared by server and client. Never duplicate it.
#
# Contains:
#   1. InventoryServicer  → base class your SERVER subclasses
#   2. InventoryStub      → object your CLIENT uses to make remote calls
#   3. add_InventoryServicer_to_server() → wires server up
# ──────────────────────────────────────────────────────────────────────────────

import grpc      # pip install grpcio
import book_pb2  # our message dataclasses (one shared copy)

# ── Serializers ───────────────────────────────────────────────────────────────
# Real protobuf uses compact binary. We use simple pipe-delimited strings.

def _serialize_request(msg):
    """StockRequest dataclass → bytes sent over the wire."""
    return msg.title.encode()                         # b"The Hobbit"

def _deserialize_request(data):
    """bytes from wire → StockRequest dataclass."""
    return book_pb2.StockRequest(title=data.decode()) # StockRequest(title="The Hobbit")

def _serialize_response(msg):
    """StockResponse dataclass → bytes sent over the wire."""
    return f"{msg.title}|{msg.amount}".encode()       # b"The Hobbit|8"

def _deserialize_response(data):
    """bytes from wire → StockResponse dataclass."""
    parts = data.decode().split("|")                  # ["The Hobbit", "8"]
    return book_pb2.StockResponse(title=parts[0], amount=int(parts[1]))

# ── SERVER SIDE ───────────────────────────────────────────────────────────────

class InventoryServicer:
    """
    Base class for the server. Subclass this and override CheckStock().
    Mirrors `service Inventory` in book.proto.
    """
    def CheckStock(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("CheckStock not implemented")
        raise NotImplementedError

def add_InventoryServicer_to_server(servicer, server):
    """
    Register the servicer with the gRPC server.
    Uses GenericRpcHandler — the correct low-level API that works on ALL grpcio versions.
    unary_unary = one request in, one response out.
    """
    # Map each RPC method name → its handler object
    rpc_method_handlers = {
        "CheckStock": grpc.unary_unary_rpc_method_handler(
            servicer.CheckStock,                          # function to call
            request_deserializer=_deserialize_request,    # bytes → StockRequest
            response_serializer=_serialize_response,      # StockResponse → bytes
        )
    }

    # Build a GenericRpcHandler that routes calls by method name
    class InventoryHandler(grpc.ServiceRpcHandler):
        def service_name(self):
            return "Inventory"                            # must match .proto service name

        def service(self, handler_call_details):
            # handler_call_details.method looks like "/Inventory/CheckStock"
            method_name = handler_call_details.method.split("/")[-1]  # → "CheckStock"
            return rpc_method_handlers.get(method_name)  # return handler or None

    server.add_generic_rpc_handlers([InventoryHandler()]) # register with grpc server

# ── CLIENT SIDE ───────────────────────────────────────────────────────────────

class InventoryStub:
    """
    Client stub — call stub.CheckStock(request) as if it's a local function.
    gRPC handles serialization, network, deserialization transparently.
    """
    def __init__(self, channel):                      # channel = open connection to server
        self.CheckStock = channel.unary_unary(        # unary_unary: 1 request → 1 response
            "/Inventory/CheckStock",                  # full route: /ServiceName/MethodName
            request_serializer=_serialize_request,    # StockRequest → bytes (outgoing)
            response_deserializer=_deserialize_response, # bytes → StockResponse (incoming)
        )
