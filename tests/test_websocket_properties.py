"""
tests/test_websocket_properties.py
=====================================
PURPOSE:
    Property-based tests for the WebSocketManager.

PROPERTIES TESTED:
    Property 11: Broadcast delivers typed event to all active connections
    Property 12: Disconnecting one client does not affect others
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


def _make_mock_websocket(will_fail: bool = False):
    """Create a mock WebSocket that records all sent messages."""
    ws = AsyncMock()
    ws.sent_messages = []

    if will_fail:
        from fastapi import WebSocketDisconnect
        ws.send_text.side_effect = WebSocketDisconnect()
    else:
        async def record_send(msg):
            ws.sent_messages.append(msg)
        ws.send_text.side_effect = record_send

    return ws


# Feature: agentic-fraud-detection, Property 11: WS broadcast on events
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
@given(
    event_type=st.sampled_from(["transaction.scored", "alert.created", "report.completed"]),
    n_clients=st.integers(min_value=1, max_value=5),
    fraud_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_property_11_broadcast_reaches_all_clients(event_type, n_clients, fraud_score):
    """
    For any event type and any number of connected clients,
    broadcast() must send the event to ALL active connections.

    Each connection must receive a message with the correct event type.

    Validates Requirement 6.2, 6.3, 6.4
    """
    from websocket_manager import WebSocketManager

    manager = WebSocketManager()

    # Create n_clients mock WebSocket connections
    clients = [_make_mock_websocket() for _ in range(n_clients)]

    async def run():
        # Connect all clients
        for ws in clients:
            ws.accept = AsyncMock()
            manager.active_connections.add(ws)
            manager._last_pong[ws] = 0

        # Broadcast an event
        payload = {"fraud_score": fraud_score, "transaction_id": "tx-123"}
        await manager.broadcast(event_type, payload)

    asyncio.run(run())

    # Property: every client must have received exactly 1 message
    for i, ws in enumerate(clients):
        assert ws.send_text.call_count == 1, (
            f"Client {i} received {ws.send_text.call_count} messages, expected 1"
        )

        # The message must contain the correct event type
        sent_msg = ws.send_text.call_args[0][0]
        parsed = json.loads(sent_msg)
        assert parsed["event"] == event_type, (
            f"Expected event '{event_type}', got '{parsed['event']}'"
        )
        assert "payload" in parsed, "Message missing 'payload' key"


# Feature: agentic-fraud-detection, Property 12: WS client isolation
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(n_clients=st.integers(min_value=2, max_value=6))
def test_property_12_client_isolation_on_disconnect(n_clients):
    """
    Disconnecting one client must not prevent remaining clients from
    receiving subsequent broadcast events.

    Validates Requirement 6.6
    """
    from websocket_manager import WebSocketManager

    manager = WebSocketManager()

    # n_clients - 1 healthy clients, 1 that will disconnect
    healthy_clients = [_make_mock_websocket(will_fail=False) for _ in range(n_clients - 1)]
    failing_client = _make_mock_websocket(will_fail=True)
    all_clients = healthy_clients + [failing_client]

    async def run():
        for ws in all_clients:
            ws.accept = AsyncMock()
            manager.active_connections.add(ws)
            manager._last_pong[ws] = 0

        # Broadcast — failing client will raise WebSocketDisconnect
        await manager.broadcast("alert.created", {"alert_id": "a-1", "fraud_score": 0.9})

    asyncio.run(run())

    # Property: all healthy clients must have received the message
    for i, ws in enumerate(healthy_clients):
        assert ws.send_text.call_count == 1, (
            f"Healthy client {i} didn't receive message after one client disconnected"
        )

    # Property: failing client must have been removed from active connections
    assert failing_client not in manager.active_connections, (
        "Disconnected client was not removed from active_connections"
    )
