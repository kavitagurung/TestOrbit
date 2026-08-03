import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Relative assets keep the static build portable for GitHub Pages project sites.
export default defineConfig({ base: './', plugins: [react()] })
