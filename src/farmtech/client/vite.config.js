import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => ({
  plugins: [
    react()
  ],
  root: path.resolve(__dirname),
  base: mode === 'production' ? '/static/dist/' : '/',
  resolve: {
    alias: {
      '@js': path.resolve(__dirname, 'js'),
      '@components': path.resolve(__dirname, 'js/components'),
      '@hooks': path.resolve(__dirname, 'js/hooks'),
      '@utils': path.resolve(__dirname, 'js/utils')
    }
  },
  build: {
    manifest: true,
    outDir: '../static/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        'farmtech-index': path.resolve(__dirname, 'js/apps/farmtech-index.jsx'),
        'farmtech-uploader': path.resolve(__dirname, 'js/apps/farmtech-uploader.jsx'),
        'farmtech-inference': path.resolve(__dirname, 'js/apps/farmtech-inference.jsx'),
        'farmtech-permission-request': path.resolve(__dirname, 'js/apps/farmtech-permission-request.jsx'),
        'farmtech-dashboard-publisher': path.resolve(__dirname, 'js/apps/farmtech-dashboard-publisher.jsx'),
        'farmtech-research': path.resolve(__dirname, 'js/apps/farmtech-research.jsx'),
      },
      output: {
        entryFileNames: 'js/[name].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: 'style/react-apps[extname]'
      }
    }
  },
  server: {
    port: 8081,
    cors: true,
    hmr: {
      host: 'localhost'
    }
  }
}));
