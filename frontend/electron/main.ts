import { app, BrowserWindow, ipcMain } from "electron"
import path from "path"
import { spawn, type ChildProcess } from "child_process"

let mainWindow: BrowserWindow | null = null
let backendProcess: ChildProcess | null = null

const IS_DEV = !app.isPackaged
const BACKEND_PORT = 18765
const FRONTEND_PORT = 5173

function getBackendPath(): string {
  if (IS_DEV) {
    // In dev, assume backend is started separately or we start it
    return path.join(app.getAppPath(), "..", "backend")
  }
  // In production, backend is bundled alongside the app
  return path.join(process.resourcesPath, "backend")
}

function startBackend(): void {
  const backendDir = getBackendPath()
  const pythonCmd = process.platform === "win32" ? "python" : "python3"

  backendProcess = spawn(pythonCmd, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)], {
    cwd: backendDir,
    stdio: IS_DEV ? "pipe" : "ignore",
    windowsHide: true,
  })

  if (IS_DEV && backendProcess.stdout) {
    backendProcess.stdout.on("data", (data: Buffer) => {
      console.log(`[backend] ${data.toString().trim()}`)
    })
  }
  if (IS_DEV && backendProcess.stderr) {
    backendProcess.stderr.on("data", (data: Buffer) => {
      console.error(`[backend] ${data.toString().trim()}`)
    })
  }

  backendProcess.on("close", (code) => {
    console.log(`[backend] process exited with code ${code}`)
    backendProcess = null
  })
}

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 960,
    minHeight: 600,
    title: "AutoAi",
    backgroundColor: "#f5f0e6",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (IS_DEV) {
    mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`)
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(app.getAppPath(), "dist", "index.html"))
  }

  mainWindow.on("closed", () => {
    mainWindow = null
  })
}

app.whenReady().then(() => {
  startBackend()
  // Give backend a moment to start before opening window
  setTimeout(createWindow, IS_DEV ? 1500 : 3000)
})

app.on("window-all-closed", () => {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
  app.quit()
})

app.on("before-quit", () => {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
})

// IPC handlers for renderer communication
ipcMain.handle("get-backend-url", () => {
  return `http://127.0.0.1:${BACKEND_PORT}`
})

ipcMain.handle("get-app-version", () => {
  return app.getVersion()
})
