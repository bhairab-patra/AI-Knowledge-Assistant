import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
    global: 'globalThis'
  },
  build: {
    outDir: 'dist',
    lib: {
      entry: resolve(__dirname, 'src/index.js'),
      name: 'ChatWidget',
      formats: ['umd'],
      fileName: 'chat-widget.umd'
    },
    rollupOptions: {
      output: {
        entryFileNames: 'chat-widget.umd.js',
        assetFileNames: '[name].[ext]'
      }
    }
  }
});
