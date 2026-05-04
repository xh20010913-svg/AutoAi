type MessageHandler = (data: any) => void

const WS_URL = "ws://localhost:18765/api/ws"

let ws: WebSocket | null = null
let handlers: Set<MessageHandler> = new Set()
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let intentionalClose = false

function getToken(): string | null {
  return localStorage.getItem("token")
}

export function connectWebSocket(onMessage: MessageHandler): () => void {
  handlers.add(onMessage)

  if (!ws || ws.readyState === WebSocket.CLOSED) {
    intentionalClose = false
    openConnection()
  }

  return () => {
    handlers.delete(onMessage)
    if (handlers.size === 0) {
      disconnectWebSocket()
    }
  }
}

function openConnection() {
  const token = getToken()
  if (!token) return

  const url = `${WS_URL}?token=${encodeURIComponent(token)}`
  ws = new WebSocket(url)

  ws.onopen = () => {
    console.log("[WS] Connected")
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      for (const handler of handlers) {
        handler(data)
      }
    } catch {
      // ignore non-JSON messages
    }
  }

  ws.onclose = () => {
    ws = null
    if (!intentionalClose && handlers.size > 0) {
      // Reconnect after 3 seconds
      reconnectTimer = setTimeout(() => {
        openConnection()
      }, 3000)
    }
  }

  ws.onerror = () => {
    // onclose will fire after error, reconnect handled there
  }
}

export function disconnectWebSocket() {
  intentionalClose = true
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (ws) {
    ws.close()
    ws = null
  }
}
