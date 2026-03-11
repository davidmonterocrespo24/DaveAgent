/**
 * WebSocket hook for DaveAgent
 * Manages WebSocket connection and message handling
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import {
  WebSocketEvent,
  WebSocketCommand,
  ConnectionStatus,
} from '../types/events';

interface UseWebSocketOptions {
  url: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

interface UseWebSocketReturn {
  events: WebSocketEvent[];
  status: ConnectionStatus;
  sendCommand: (command: WebSocketCommand) => void;
  sendMessage: (message: string) => void;
  clearEvents: () => void;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Custom hook for WebSocket connection to DaveAgent backend
 *
 * @param options - Configuration options
 * @returns WebSocket state and control functions
 *
 * @example
 * ```tsx
 * const { events, status, sendMessage } = useWebSocket({
 *   url: 'ws://localhost:8000/ws/agent'
 * });
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    autoConnect = true,
    reconnectAttempts = 3,
    reconnectDelay = 2000,
  } = options;

  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>('connecting');

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected');
      return;
    }

    console.log(`[WebSocket] Connecting to ${url}...`);
    setStatus('connecting');

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WebSocket] Connected');
        setStatus('connected');
        reconnectCountRef.current = 0; // Reset reconnect counter
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketEvent;
          console.log('[WebSocket] Received event:', data.type);

          setEvents((prev) => [...prev, data]);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        setStatus('error');
      };

      ws.onclose = (event) => {
        console.log('[WebSocket] Disconnected', event.code, event.reason);
        setStatus('disconnected');

        // Attempt reconnection
        if (
          reconnectCountRef.current < reconnectAttempts &&
          !event.wasClean
        ) {
          reconnectCountRef.current++;
          console.log(
            `[WebSocket] Reconnecting (${reconnectCountRef.current}/${reconnectAttempts})...`
          );

          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect();
          }, reconnectDelay);
        }
      };
    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      setStatus('error');
    }
  }, [url, reconnectAttempts, reconnectDelay]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      console.log('[WebSocket] Disconnecting...');
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  /**
   * Send a command to the server
   */
  const sendCommand = useCallback((command: WebSocketCommand) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = JSON.stringify(command);
      console.log('[WebSocket] Sending command:', command.command);
      wsRef.current.send(message);
    } else {
      console.error('[WebSocket] Cannot send - not connected');
    }
  }, []);

  /**
   * Send a message (convenience wrapper for execute command)
   */
  const sendMessage = useCallback(
    (message: string) => {
      sendCommand({
        command: 'execute',
        content: message,
      });
    },
    [sendCommand]
  );

  /**
   * Clear all events
   */
  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  /**
   * Auto-connect on mount
   */
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    events,
    status,
    sendCommand,
    sendMessage,
    clearEvents,
    connect,
    disconnect,
  };
}
