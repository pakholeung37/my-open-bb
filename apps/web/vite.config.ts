import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, ".", "");
	const proxyTarget = env.VITE_PROXY_TARGET ?? "http://127.0.0.1:8000";

	return {
		plugins: [react()],
		server: {
			host: "0.0.0.0",
			port: 7000,
			proxy: {
				"/api": {
					target: proxyTarget,
					changeOrigin: true,
				},
			},
		},
		test: {
			environment: "jsdom",
			globals: true,
		},
	};
});
