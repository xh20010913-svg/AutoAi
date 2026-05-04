import { useEffect, useRef, useCallback, useState } from "react"

export interface WSLogEntry {
  run_id: string
  timestamp: string
  level: "info" | "warn" | "error"
  message: string
}

export interface WSRunEvent {
  type: "run_started" | "run_finished"
  run_id: string
  agent_id: string
  agent_name: string
  task_id?: string
  task_title?: string
  status: string
  timestamp: string
}

export type WSMessage = WSLogEntry | WSRunEvent

const WS_URL = "ws://localhost:18765/api/v1/ws"

export function useWebSocket(onMessage?: (msg: WSMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        setConnected(true)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSMessage
          onMessageRef.current?.(data)
        } catch {
          // ignore malformed messages
        }
      }

      ws.onclose = () => {
        setConnected(false)
        // Reconnect after 3s
        reconnectTimer.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        ws.close()
      }

      wsRef.current = ws
    } catch {
      // WebSocket not available, will retry
      reconnectTimer.current = setTimeout(connect, 3000)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { connected }
}
