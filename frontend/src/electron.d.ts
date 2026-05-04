interface AutoaiAPI {
  getBackendUrl(): Promise<string>
  getAppVersion(): Promise<string>
  platform: string
}

declare global {
  interface Window {
    autoai?: AutoaiAPI
  }
}

export {}
