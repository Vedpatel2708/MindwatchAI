'use client';
/**
 * frontend/components/WebSocketProvider.tsx
 * ==========================================
 * PURPOSE:
 *   Establishes and maintains the WebSocket connection to the FastAPI backend.
 *   Exposes a React context so any component can subscribe to real-time events
 *   (transaction.scored, alert.created, report.completed) without managing the
 *   connection themselves.
 *
 * ARCHITECTURE ROLE:
 *   Wraps the entire app (mounted in layout.tsx). Any component calls
 *   useWebSocket() to subscribe to specific event types and receive live data.
 *
 * DESIGN DECISIONS:
 *   Exponential backoff (Req 7.8):
 *     On disconnect, we wait 1s before retry, doubling each attempt up to 30s max.
 *     Formula: min(initialDelay * 2^k, maxDelay) where k = failure count.
 *     This prevents hammering the server with reconnect attempts during downtime.
 *
 *   Event subscription map:
 *     Subscribers register a handler function for a specific event type string.
 *     When a WS message arrives with that event type, the handler is called.
 *     Multiple components can subscribe to the same event type independently.
 *
 *   Pong response:
 *     When the server sends {"event": "ping"}, we respond with {"event": "pong"}
 *     to keep the connection alive (Req 6.5).
 */

import React, {
  createContext,      // createContext: creates the React context object
  useCallback,        // useCallback: memoises functions to prevent re-renders
  useContext,         // useContext: hook to consume the context in child components
  useEffect,          // useEffect: runs side effects (WS connection) after render
  useRef,             // useRef: holds mutable values that don't trigger re-renders
  useState,           // useState: tracks connection and reconnecting state
} from 'react';

// =============================================================================
// CONTEXT TYPE DEFINITION
// =============================================================================

/** The shape of data provided to consumers via useWebSocket() */
interface WebSocketContextValue {
  /**
   * Subscribe to a specific event type.
   *
   * @param eventType - The event type string (e.g. "transaction.scored")
   * @param handler   - Callback receiving the event payload object
   * @returns         Unsubscribe function — call it in useEffect cleanup
   *
   * Example:
   *   const unsubscribe = subscribe('alert.created', (payload) => {
   *     setAlerts(prev => [payload, ...prev]);
   *   });
   *   return unsubscribe; // cleanup on component unmount
   */
  subscribe: (eventType: string, handler: (payload: unknown) => void) => () => void;

  /** True when the WebSocket connection is established and ready */
  isConnected: boolean;

  /** True when a reconnection attempt is in progress */
  isReconnecting: boolean;
}

// Create the context with a default value (used if consumed outside the provider)
const WebSocketContext = createContext<WebSocketContextValue>({
  subscribe: () => () => {},
  isConnected: false,
  isReconnecting: false,
});

// =============================================================================
// PROVIDER COMPONENT
// =============================================================================

/** Props for WebSocketProvider */
interface WebSocketProviderProps {
  children: React.ReactNode;
}

/**
 * WebSocketProvider: establishes the WS connection and manages reconnection.
 *
 * Mount this at the root of your app (layout.tsx) so all pages share
 * a single connection and receive events throughout the session.
 */
export function WebSocketProvider({ children }: WebSocketProviderProps) {
  // isConnected: true when WS is open and usable
  const [isConnected, setIsConnected] = useState(false);

  // isReconnecting: true during the backoff period between disconnect and reconnect
  const [isReconnecting, setIsReconnecting] = useState(false);

  // wsRef: holds the WebSocket instance across renders without triggering re-renders
  // useRef because we don't want reconnect to cause a full component re-render
  const wsRef = useRef<WebSocket | null>(null);

  // retryDelayRef: tracks current backoff delay — starts at 2s
  const retryDelayRef = useRef<number>(2000);

  // retryTimerRef: holds the setTimeout ID for the reconnect timer
  // We need to store it so we can clear it on unmount (cleanup)
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // subscribersRef: Map of eventType → Set of handler functions
  // useRef because modifying subscribers shouldn't trigger re-renders
  // Map<string, Set<Function>> allows multiple components to subscribe to the same event
  const subscribersRef = useRef<Map<string, Set<(payload: unknown) => void>>>(new Map());

  /**
   * Connect to the WebSocket server.
   * Called on mount and after each reconnect delay.
   */
  const connect = useCallback(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

    // Close any existing connection before creating a new one
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      wsRef.current.close();
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      // Connection established — reset backoff and update state
      setIsConnected(true);
      setIsReconnecting(false);
      retryDelayRef.current = 1000; // reset delay on successful connect
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data as string) as {
          event: string;
          payload?: unknown;
        };

        // Respond to server heartbeat pings with a pong (Req 6.5)
        if (message.event === 'ping') {
          ws.send(JSON.stringify({ event: 'pong' }));
          return;
        }

        // Dispatch to all subscribers for this event type
        const handlers = subscribersRef.current.get(message.event);
        if (handlers) {
          handlers.forEach(handler => handler(message.payload));
        }
      } catch (err) {
        // Ignore malformed messages — don't crash the connection
        console.warn('WebSocket: failed to parse message', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsReconnecting(true);

      // Exponential backoff: 2s → 4s → 8s → ... max 30s
      // Start at 2s (not 1s) to avoid rapid reconnect loops
      retryTimerRef.current = setTimeout(() => {
        retryDelayRef.current = Math.min(retryDelayRef.current * 2, 30000);
        connect();
      }, retryDelayRef.current);
    };

    ws.onerror = () => {
      // onerror is always followed by onclose — let onclose handle reconnect
      // We just log here for debugging
      console.warn('WebSocket error — will reconnect via onclose handler');
    };
  }, []); // empty deps: connect function never changes

  // Connect on mount, cleanup on unmount
  useEffect(() => {
    connect();

    return () => {
      // Clear any pending reconnect timer
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current);
      }
      // Close the WebSocket cleanly on unmount
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  /**
   * Subscribe to a specific WebSocket event type.
   *
   * Returns an unsubscribe function — call it in useEffect cleanup to prevent
   * memory leaks when the subscribing component unmounts.
   */
  const subscribe = useCallback(
    (eventType: string, handler: (payload: unknown) => void) => {
      // Get or create the Set of handlers for this event type
      if (!subscribersRef.current.has(eventType)) {
        subscribersRef.current.set(eventType, new Set());
      }
      subscribersRef.current.get(eventType)!.add(handler);

      // Return unsubscribe function (for useEffect cleanup)
      return () => {
        subscribersRef.current.get(eventType)?.delete(handler);
      };
    },
    [] // stable reference — subscribe function never changes
  );

  return (
    <WebSocketContext.Provider value={{ subscribe, isConnected, isReconnecting }}>
      {children}
    </WebSocketContext.Provider>
  );
}

// =============================================================================
// CUSTOM HOOK
// =============================================================================

/**
 * useWebSocket — consume the WebSocket context in any component.
 *
 * Usage:
 *   const { subscribe, isConnected, isReconnecting } = useWebSocket();
 *
 *   useEffect(() => {
 *     const unsub = subscribe('alert.created', (payload) => {
 *       console.log('New alert:', payload);
 *     });
 *     return unsub; // cleanup on unmount
 *   }, [subscribe]);
 */
export function useWebSocket(): WebSocketContextValue {
  return useContext(WebSocketContext);
}
