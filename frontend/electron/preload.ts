import { contextBridge, ipcRenderer } from "electron"

const BACKEND_PORT = 18765

contextBridge.exposeInMainWorld("autoai", {
  getBackendUrl: () => ipcRenderer.invoke("get-backend-url"),
  getBackendUrlSync: () => `http://127.0.0.1:${BACKEND_PORT}`,
  getAppVersion: () => ipcRenderer.invoke("get-app-version"),
  platform: process.platform,
})
