type MessageHandler = (data: any) => void

let ws: WebSocket | null = null
let handlers: Set<MessageHandler> = new Set()
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let intentionalClose = false
let reconnectAttempts = 0
const MAX_RECONNECT_DELAY = 30000

function getBaseUrl(): string {
  if (typeof window !== "undefined" && window.autoai) {
    return window.autoai.getBackendUrlSync?.() ?? "http://localhost:18765"
  }
  return "http://localhost:18765"
}

function getWsUrl(): string {
  const base = getBaseUrl()
  return base.replace(/^http/, "ws") + "/api/v1/ws"
}

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

  const url = `${getWsUrl()}?token=${encodeURIComponent(token)}`
  ws = new WebSocket(url)

  ws.onopen = () => {
    console.log("[WS] Connected")
    reconnectAttempts = 0
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
      const delay = Math.min(1000 * 2 ** reconnectAttempts, MAX_RECONNECT_DELAY)
      reconnectAttempts++
      console.log(`[WS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`)
      reconnectTimer = setTimeout(() => {
        openConnection()
      }, delay)
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
