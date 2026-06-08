"""
backend/websocket_manager.py
=============================
PURPOSE:
    Manages all active WebSocket connections and broadcasts real-time events
    to the frontend dashboard. This is the "pub/sub" layer of the system.

ARCHITECTURE ROLE:
    When transactions are scored, alerts are created, or investigation reports
    complete, the routers/agent call `ws_manager.broadcast(event_type, payload)`.
    This module fans out those events to every connected browser client instantly.

    Without this module, the dashboard would need to poll the API every few
    seconds — wasteful and slow. With WebSockets, updates arrive in <100ms.

DESIGN DECISIONS:
    asyncio.gather for broadcast (Req 6.2-6.4):
        Sending to all clients concurrently (not sequentially) ensures that
        one slow client doesn't delay delivery to all other clients.

    Heartbeat mechanism (Req 6.5):
        WebSocket connections can go stale — the TCP connection appears open
        but the browser has actually navigated away or the network changed.
        We ping every 30s and close connections that don't pong within 60s.

    Silent disconnect handling (Req 6.6):
        If a client disconnects mid-broadcast, we catch WebSocketDisconnect
        silently and remove it from the active set. Other clients are unaffected.
"""

# asyncio: Python's async I/O library.
# We use asyncio.gather() to send to all clients concurrently.
import asyncio

# json: serialising event payloads to JSON strings for WebSocket transmission.
import json

# logging: recording connection events and broadcast errors.
import logging

# time: tracking last_pong timestamps for stale connection detection.
import time

# Set: used for the active connections collection (O(1) add/remove/check).
from typing import Set

# WebSocket: FastAPI's WebSocket connection object.
# WebSocketDisconnect: exception raised when a client disconnects unexpectedly.
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages a set of active WebSocket connections and broadcasts events.

    This class is instantiated ONCE at module level (see bottom of file)
    and imported by main.py and the routers/agent that need to broadcast.

    Thread/async safety:
        All methods are async — they run in FastAPI's event loop.
        The `active_connections` set is modified only within async context,
        which is single-threaded in Python's asyncio model. No locks needed.
    """

    def __init__(self):
        # Set of active WebSocket connections.
        # A set gives O(1) add/remove, important for high-throughput systems.
        self.active_connections: Set[WebSocket] = set()

        # Track the last pong time per connection for heartbeat/stale detection.
        # Key: WebSocket object, Value: unix timestamp of last received pong
        self._last_pong: dict[WebSocket, float] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        Called by the /ws endpoint handler in main.py when a client connects.

        Args:
            websocket: The incoming WebSocket connection from FastAPI.

        Side effects:
            - Accepts the WebSocket handshake (sends HTTP 101 Switching Protocols)
            - Adds the connection to active_connections
            - Records the current time as the initial "last pong" time
        """
        # accept() completes the WebSocket handshake.
        # Until accept() is called, no data can be sent/received on this WS.
        await websocket.accept()

        # Add to the active set so broadcasts include this client
        self.active_connections.add(websocket)

        # Initialise last_pong to now — prevents immediate stale detection
        self._last_pong[websocket] = time.time()

        logger.info(f"WebSocket connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from the active set.

        Called when a client disconnects (either intentionally or due to
        network failure). Safe to call even if the connection is already removed.

        Args:
            websocket: The disconnected WebSocket connection.

        Side effects:
            - Removes from active_connections (no-op if already removed)
            - Removes from _last_pong tracking dict
        """
        # discard() is safe — won't raise KeyError if not in the set
        self.active_connections.discard(websocket)
        self._last_pong.pop(websocket, None)   # None = don't raise if missing

        logger.info(f"WebSocket disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, payload: dict) -> None:
        """
        Send a typed event to ALL currently connected WebSocket clients.

        Event format:
            {"event": "<event_type>", "payload": {<payload dict>}}

        Event types used by this system:
            "transaction.scored" — ML scoring complete (Req 6.2)
            "alert.created"      — fraud threshold exceeded (Req 6.3)
            "report.completed"   — agent investigation done (Req 6.4)

        Args:
            event_type: String identifier for the event type.
            payload:    Dict of event-specific data fields.

        Side effects:
            - Sends JSON message to all active connections.
            - Disconnects and removes stale clients that raise WebSocketDisconnect.
        """
        if not self.active_connections:
            # No clients connected — skip serialisation entirely (fast path)
            return

        # Build the message once, then reuse the same string for all clients.
        # Serialising JSON is cheap but there's no reason to do it N times.
        message = json.dumps({"event": event_type, "payload": payload})

        # Collect clients that fail to receive the message for cleanup
        disconnected: list[WebSocket] = []

        # asyncio.gather sends to all clients CONCURRENTLY.
        # WHY CONCURRENTLY? If we send sequentially (for ws in connections: await ws.send_text())
        # then a slow client blocks delivery to all subsequent clients.
        # With gather, all sends start immediately and we wait for all to finish.
        async def _send(ws: WebSocket) -> None:
            try:
                await ws.send_text(message)
            except WebSocketDisconnect:
                # Client disconnected during the send — mark for removal
                disconnected.append(ws)
            except Exception as exc:
                # Any other error (e.g. connection reset) — also remove client
                logger.warning(f"WebSocket send error: {exc}")
                disconnected.append(ws)

        # Create send coroutines for all connections, run concurrently
        await asyncio.gather(*[_send(ws) for ws in self.active_connections])

        # Clean up disconnected clients after the broadcast loop
        # (can't modify the set while iterating over it)
        for ws in disconnected:
            self.disconnect(ws)

        if disconnected:
            logger.debug(f"Removed {len(disconnected)} stale connections after broadcast.")

    async def send_heartbeat(self) -> None:
        """
        Background task that pings all active connections every 30 seconds
        and closes connections that haven't responded within 60 seconds.

        WHY A HEARTBEAT?
            TCP connections can appear open at the OS level but the browser
            may have already closed (navigated away, tab closed, network change).
            Without heartbeats, the server accumulates "zombie" connections
            that waste memory and cause broadcast errors.

        Heartbeat protocol:
            Server → Client: text message {"event": "ping"}    (every 30s)
            Client → Server: text message {"event": "pong"}    (expected within 60s)
            If no pong received within 60s → close the connection

        This runs as a FastAPI BackgroundTask started in main.py's startup handler.
        (Requirement 6.5)

        Side effects:
            - Sends ping to all active connections every 30 seconds.
            - Closes connections that don't respond within 60 seconds.
        """
        PING_INTERVAL_SECONDS = 30   # send a ping every 30 seconds
        PONG_TIMEOUT_SECONDS = 60    # close if no pong within 60 seconds

        while True:
            # Wait before the first ping so startup isn't immediately pinged
            await asyncio.sleep(PING_INTERVAL_SECONDS)

            now = time.time()
            stale: list[WebSocket] = []

            for ws in list(self.active_connections):
                # Check if the client's last pong is older than the timeout
                last_pong = self._last_pong.get(ws, now)
                if now - last_pong > PONG_TIMEOUT_SECONDS:
                    # Client hasn't ponged in 60s — assume it's dead
                    stale.append(ws)
                    continue

                # Send a ping message to this client
                try:
                    await ws.send_text(json.dumps({"event": "ping"}))
                except Exception:
                    # Failed to send ping — connection is definitely dead
                    stale.append(ws)

            # Close all stale connections
            for ws in stale:
                try:
                    await ws.close(code=1001)  # 1001 = "Going Away"
                except Exception:
                    pass  # already closed — ignore
                self.disconnect(ws)

            if stale:
                logger.info(f"Heartbeat: closed {len(stale)} stale connections.")

    def record_pong(self, websocket: WebSocket) -> None:
        """
        Update the last_pong timestamp when a client sends a pong message.

        Called by the /ws endpoint handler in main.py when it receives
        a message with {"event": "pong"} from the client.

        Args:
            websocket: The WebSocket that sent the pong.
        """
        self._last_pong[websocket] = time.time()


# ---------------------------------------------------------------------------
# MODULE-LEVEL SINGLETON
# ---------------------------------------------------------------------------
# Create one shared WebSocketManager — imported by main.py, routers, and agent.
# All broadcasts go through this single instance.
ws_manager = WebSocketManager()
