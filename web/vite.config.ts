import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// Spike: the React rebuild of the player. During the migration the existing
// node server (tools/server.mjs on :4747) still owns the agent chat, track
// files, and audio endpoints — so we proxy those routes through Vite's dev
// server and the React app talks to them unchanged.
const BACKEND = 'http://localhost:4747';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5273,
    proxy: {
      '/api': BACKEND,
      '/tracks': BACKEND,
      '/sections': BACKEND,
      '/audio': BACKEND,
      '/save-wav': BACKEND,
      '/upload-buffer': BACKEND,
      '/log': BACKEND,
    },
  },
});
