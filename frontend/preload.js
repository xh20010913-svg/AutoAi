const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("autoai", {
  backendUrl: "http://127.0.0.1:18765",
});
