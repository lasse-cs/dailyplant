import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
    base: "/static/",
    root: resolve(__dirname, "src/static_src"),
    publicDir: false,
    resolve: {
        alias: {
            "@": resolve(__dirname, "src/static_src/"),
        },
    },
    server: {
        origin: "http://localhost:5173",
        cors: {
            origin: "http://localhost:8000",
        },
    },
    build: {
        manifest: true,
        outDir: resolve(__dirname, "src/static_built/"),
        rolldownOptions: {
            input: {
                main: resolve(__dirname, "src/static_src/js/main.js"),
                archive: resolve(__dirname, "src/static_src/js/archive.js"),
            },
            output: {
                entryFileNames: `js/[name].js`,
                chunkFileNames: `js/[name].js`,
                assetFileNames: `assets/[name][extname]`,
            },
        },
    },
});