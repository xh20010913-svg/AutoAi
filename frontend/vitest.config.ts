import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: [
        'src/components/LoginForm.tsx',
        'src/components/TaskCard.tsx',
        'src/components/AgentCard.tsx',
        'src/components/pixel/PixelCharacter.tsx',
        'src/components/layout/Sidebar.tsx',
      ],
    },
  },
})
