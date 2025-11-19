import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		port: 5173,
		host: true
	},
	preview: {
		port: 4173,
		host: true
	},
	optimizeDeps: {
		include: ['mermaid', 'codemirror']
	}
});