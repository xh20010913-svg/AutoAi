import { app, BrowserWindow } from "electron";
import { spawn, type ChildProcess } from "child_process";
import path from "node:path";

let backendProcess: ChildProcess | null = null;
const BACKEND_PORT = 18765;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

function startBackend(): Promise<void> {
  return new Promise((resolve, reject) => {
    backendProcess = spawn(
      "python",
      ["-m", "autoai", "serve", "--port", String(BACKEND_PORT)],
      {
        cwd: path.join(__dirname, ".."),
        stdio: ["ignore", "pipe", "pipe"],
      }
    );

    backendProcess.stdout?.on("data", (data: Buffer) => {
      const text = data.toString();
      console.log(`[backend] ${text}`);
      if (text.includes("Uvicorn running")) {
        resolve();
      }
    });

    backendProcess.stderr?.on("data", (data: Buffer) => {
      console.error(`[backend stderr] ${data.toString()}`);
    });

    backendProcess.on("error", (err: Error) => {
      console.error("Failed to start backend:", err);
      reject(err);
    });

    setTimeout(resolve, 3000);
  });
}

function waitForBackend(url: string, maxRetries = 30): Promise<void> {
  return new Promise((resolve) => {
    let retries = 0;
    const check = () => {
      fetch(`${url}/api/status?project_dir=`)
        .then(() => resolve())
        .catch(() => {
          retries++;
          if (retries < maxRetries) {
            setTimeout(check, 200);
          } else {
            resolve();
          }
        });
    };
    check();
  });
}

async function createWindow() {
  await startBackend();
  await waitForBackend(BACKEND_URL);

  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 600,
    backgroundColor: "#0f0f1a",
    title: "AutoAI",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (process.env.VITE_DEV_SERVER_URL) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(path.join(__dirname, "../dist/index.html"));
  }

  win.on("closed", () => {
    if (backendProcess) {
      backendProcess.kill();
      backendProcess = null;
    }
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
  app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
});
