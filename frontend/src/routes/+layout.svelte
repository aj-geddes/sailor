<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { ModeWatcher } from 'mode-watcher';
	import { Toaster } from 'svelte-sonner';
	import { websocketService } from '$lib/services/websocket';
	import Navigation from '$lib/components/Navigation.svelte';

	// Connect WebSocket on mount
	onMount(() => {
		if (typeof window !== 'undefined') {
			websocketService.connect().catch(console.error);
		}

		return () => {
			websocketService.disconnect();
		};
	});
</script>

<ModeWatcher />
<Toaster richColors position="bottom-right" />

<div class="app">
	<Navigation />
	<main>
		<slot />
	</main>
</div>

<style>
	.app {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
		background: var(--background);
		color: var(--foreground);
	}

	main {
		flex: 1;
		display: flex;
		flex-direction: column;
	}

	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu,
			Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
	}

	:global(:root) {
		--background: hsl(0 0% 100%);
		--foreground: hsl(240 10% 3.9%);
		--card: hsl(0 0% 100%);
		--card-foreground: hsl(240 10% 3.9%);
		--popover: hsl(0 0% 100%);
		--popover-foreground: hsl(240 10% 3.9%);
		--primary: hsl(240 5.9% 10%);
		--primary-foreground: hsl(0 0% 98%);
		--secondary: hsl(240 4.8% 95.9%);
		--secondary-foreground: hsl(240 5.9% 10%);
		--muted: hsl(240 4.8% 95.9%);
		--muted-foreground: hsl(240 3.8% 46.1%);
		--accent: hsl(240 4.8% 95.9%);
		--accent-foreground: hsl(240 5.9% 10%);
		--destructive: hsl(0 84.2% 60.2%);
		--destructive-foreground: hsl(0 0% 98%);
		--border: hsl(240 5.9% 90%);
		--input: hsl(240 5.9% 90%);
		--ring: hsl(240 10% 3.9%);
		--radius: 0.5rem;
	}

	:global(.dark) {
		--background: hsl(240 10% 3.9%);
		--foreground: hsl(0 0% 98%);
		--card: hsl(240 10% 3.9%);
		--card-foreground: hsl(0 0% 98%);
		--popover: hsl(240 10% 3.9%);
		--popover-foreground: hsl(0 0% 98%);
		--primary: hsl(0 0% 98%);
		--primary-foreground: hsl(240 5.9% 10%);
		--secondary: hsl(240 3.7% 15.9%);
		--secondary-foreground: hsl(0 0% 98%);
		--muted: hsl(240 3.7% 15.9%);
		--muted-foreground: hsl(240 5% 64.9%);
		--accent: hsl(240 3.7% 15.9%);
		--accent-foreground: hsl(0 0% 98%);
		--destructive: hsl(0 62.8% 30.6%);
		--destructive-foreground: hsl(0 0% 98%);
		--border: hsl(240 3.7% 15.9%);
		--input: hsl(240 3.7% 15.9%);
		--ring: hsl(240 4.9% 83.9%);
	}
</style>