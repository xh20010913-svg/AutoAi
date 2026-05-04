import { useEffect, useState, useCallback } from "react"

export type ToastType = "success" | "error" | "info"

interface Toast {
  id: number
  message: string
  type: ToastType
}

let toastId = 0
let listeners: Set<() => void> = new Set()
let toasts: Toast[] = []

function notify() {
  for (const l of listeners) l()
}

export function showToast(message: string, type: ToastType = "info") {
  const id = ++toastId
  toasts = [...toasts, { id, message, type }]
  notify()
  setTimeout(() => {
    toasts = toasts.filter((t) => t.id !== id)
    notify()
  }, 4000)
}

export function dismissToast(id: number) {
  toasts = toasts.filter((t) => t.id !== id)
  notify()
}

export function useToasts() {
  const [, setTick] = useState(0)
  useEffect(() => {
    const handler = () => setTick((t) => t + 1)
    listeners.add(handler)
    return () => { listeners.delete(handler) }
  }, [])
  return toasts
}
