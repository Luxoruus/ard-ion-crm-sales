import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  build: {
    rollupOptions: {
    //   input: resolve(__dirname, 'SurveyPage.vue'),
      output: {
        entryFileNames: 'js/survey.bundle.js', // Output to public/js/
        format: 'es'
      }
    },
    // outDir: resolve(__dirname, '../js'),
    outDir: resolve('../'),
    emptyOutDir: false
  }
})