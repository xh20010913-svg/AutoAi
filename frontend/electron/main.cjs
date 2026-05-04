const { app, BrowserWindow, ipcMain } = require("electron")
const path = require("path")
const { spawn } = require("child_process")
const http = require("http")

let mainWindow = null
let backendProcess = null

const IS_DEV = !app.isPackaged
const BACKEND_PORT = 8000
const FRONTEND_PORT = 5173

function getBackendPath() {
  if (IS_DEV) {
    return path.join(app.getAppPath(), "..", "backend")
  }
  return path.join(process.resourcesPath, "backend")
}

function checkBackend(callback) {
  const req = http.get("http://127.0.0.1:" + BACKEND_PORT + "/api/v1/health", (res) => {
    callback(res.statusCode === 200)
  })
  req.on("error", () => callback(false))
  req.setTimeout(2000, () => { req.destroy(); callback(false) })
}

function startBackend() {
  const backendDir = getBackendPath()
  // Try python3 first, fall back to python
  const candidates = ["python3", "python"]

  for (const cmd of candidates) {
    try {
      backendProcess = spawn(cmd, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)], {
        cwd: backendDir,
        stdio: IS_DEV ? "pipe" : "ignore",
        windowsHide: true,
      })

      if (backendProcess.pid) {
        console.log("[electron] Backend started with " + cmd + " (PID: " + backendProcess.pid + ")")

        if (IS_DEV && backendProcess.stdout) {
          backendProcess.stdout.on("data", (data) => {
            console.log("[backend] " + data.toString().trim())
          })
        }
        if (IS_DEV && backendProcess.stderr) {
          backendProcess.stderr.on("data", (data) => {
            console.error("[backend] " + data.toString().trim())
          })
        }

        backendProcess.on("close", (code) => {
          console.log("[backend] process exited with code " + code)
          backendProcess = null
        })
        return
      }
    } catch (e) {
      // try next candidate
    }
  }
  console.error("[electron] Could not start backend - no python found")
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 960,
    minHeight: 600,
    title: "AutoAi",
    backgroundColor: "#f5f0e6",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (IS_DEV) {
    mainWindow.loadURL("http://localhost:" + FRONTEND_PORT)
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(app.getAppPath(), "dist", "index.html"))
  }

  mainWindow.on("closed", () => {
    mainWindow = null
  })
}

app.whenReady().then(() => {
  checkBackend((running) => {
    if (!running) {
      console.log("[electron] Backend not running, starting it...")
      startBackend()
    } else {
      console.log("[electron] Backend already running on port " + BACKEND_PORT)
    }
    // Give backend time to initialize, then create window
    setTimeout(createWindow, running ? 500 : 3000)
  })
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

ipcMain.handle("get-backend-url", () => {
  return "http://127.0.0.1:" + BACKEND_PORT
})

ipcMain.handle("get-app-version", () => {
  return app.getVersion()
})
