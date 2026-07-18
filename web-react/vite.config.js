import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    // The radiating burst scene is optional and lazy, keeping the timing
    // dashboard independent from the heavier 3D runtime on first render.
    chunkSizeWarningLimit: 850,
  },
});
