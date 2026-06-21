import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { VitePWA } from "vite-plugin-pwa";

const devApiUrl = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      // injectManifest: we supply our own sw.js with full workbox control.
      strategies: "injectManifest",
      srcDir: ".",          // sw.js lives at client/sw.js (root of the client dir)
      filename: "sw.js",
      registerType: "prompt",   // let our code handle registration timing
      injectRegister: false,    // we register manually in index.js

      // Copy offline.html into the dist root so the SW can serve it.
      includeAssets: [
        "offline.html",
        "assets/favicon.ico",
        "assets/apple-touch-icon.png",
      ],

      manifest: {
        name: "Flatnotes Enhanced",
        short_name: "flatnotes",
        description:
          "A self-hosted, feature-rich note-taking app with folders, nested tags, and offline support.",
        theme_color: "#F8A66B",
        background_color: "#ffffff",
        display: "standalone",
        start_url: "/",
        scope: "/",
        icons: [
          {
            src: "assets/android-chrome-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "assets/android-chrome-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
          {
            src: "assets/apple-touch-icon.png",
            sizes: "180x180",
            type: "image/png",
          },
        ],
      },

      workbox: {
        // Precache patterns: everything in the dist root + hashed JS/CSS bundles
        globPatterns: [
          "**/*.{js,css,html,woff2,woff,ttf,png,svg,ico,webp}",
        ],
        // Don't precache the service worker itself or the dev sourcemaps
        globIgnores: ["sw.js", "workbox-*.js"],
      },
    }),
  ],

  root: "client",
  base: "",

  server: {
    // Note: The FLATNOTES_PATH_PREFIX environment variable is not supported by the dev server
    port: 8080,
    proxy: {
      "/api/": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/attachments/": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/docs": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/openapi.json": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/health": {
        target: devApiUrl,
        changeOrigin: true,
      },
    },
  },
});
