import { contextBridge, ipcRenderer } from "electron"

contextBridge.exposeInMainWorld("autoai", {
  getBackendUrl: () => ipcRenderer.invoke("get-backend-url"),
  getAppVersion: () => ipcRenderer.invoke("get-app-version"),
  platform: process.platform,
})
