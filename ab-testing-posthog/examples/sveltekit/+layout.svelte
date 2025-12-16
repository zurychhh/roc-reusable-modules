<script lang="ts">
	/**
	 * SvelteKit Root Layout - PostHog Initialization
	 *
	 * Initialize PostHog once in the root layout.
	 * This ensures PostHog is available across all pages.
	 */
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { initPostHog } from '$lib/posthog';

	// Initialize analytics tracking
	onMount(() => {
		if (browser) {
			initPostHog();
		}
	});
</script>

<slot />
