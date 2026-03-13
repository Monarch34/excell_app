import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import compression from 'vite-plugin-compression'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '')
    const apiTarget = (env.VITE_API_TARGET || '').trim()

    return {
        plugins: [
            vue(),
            compression({ algorithm: 'gzip', threshold: 1024 }),
            compression({ algorithm: 'brotliCompress', ext: '.br', threshold: 1024 }),
        ],
        build: {
            // Plotly is intentionally large and loaded in a dedicated lazy chunk.
            chunkSizeWarningLimit: 5000,
            rollupOptions: {
                output: {
                    manualChunks(id) {
                        // Keep only the heavy Plotly bundle isolated.
                        // Let Rollup decide remaining vendor graph to avoid
                        // chunk-circular warnings from over-aggressive manual grouping.
                        if (id.includes('plotly.js-dist-min')) return 'plotly'
                    }
                }
            }
        },
        resolve: {
            alias: {
                '@': fileURLToPath(new URL('./src', import.meta.url))
            }
        },
        server: {
            proxy: apiTarget ? {
                '/api': {
                    target: apiTarget,
                    changeOrigin: true,
                },
            } : undefined,
            watch: env.VITE_USE_POLLING === 'true' ? {
                usePolling: true,
            } : undefined,
        },
    }
})
