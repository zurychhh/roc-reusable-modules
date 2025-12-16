<script lang="ts">
	/**
	 * Example A/B Test Component for SvelteKit (Svelte 5)
	 *
	 * This component demonstrates how to implement an A/B test
	 * with PostHog feature flags.
	 */
	import { onMount } from 'svelte';
	import posthog from 'posthog-js';
	import { setActiveExperiment, trackExperimentImpression } from '$lib/utils/analytics';

	// Experiment configuration
	const EXPERIMENT_KEY = 'hero-headline-test';

	// Svelte 5 runes for state
	let variant = $state('control');
	let isLoaded = $state(false);

	// Define your variants
	const variants = {
		control: {
			headline: 'Original Headline',
			subheadline: 'Original subheadline text'
		},
		variant_a: {
			headline: 'New Headline A',
			subheadline: 'Alternative subheadline for variant A'
		},
		variant_b: {
			headline: 'New Headline B',
			subheadline: 'Alternative subheadline for variant B'
		}
	};

	// Current variant content
	let content = $derived(variants[variant as keyof typeof variants] || variants.control);

	onMount(() => {
		// Timeout fallback - show control after 1.5s if PostHog doesn't load
		const timeout = setTimeout(() => {
			if (!isLoaded) {
				isLoaded = true;
				console.log('[A/B Test] Fallback to control (timeout)');
			}
		}, 1500);

		// Wait for PostHog feature flags
		posthog.onFeatureFlags(() => {
			clearTimeout(timeout);

			// Get assigned variant
			const flag = posthog.getFeatureFlag(EXPERIMENT_KEY);
			variant = (flag as string) || 'control';
			isLoaded = true;

			console.log(`[A/B Test] ${EXPERIMENT_KEY} = ${variant}`);

			// Track impression (PostHog does this automatically, but we also send to GTM)
			posthog.capture('$experiment_started', {
				experiment: EXPERIMENT_KEY,
				variant: variant
			});

			// Track in GTM dataLayer
			trackExperimentImpression({
				experimentId: EXPERIMENT_KEY,
				experimentName: 'Hero Headline Test',
				variantId: variant,
				variantName: variant
			});

			// Store for backend/CRM
			setActiveExperiment(EXPERIMENT_KEY, variant);
		});
	});
</script>

{#if !isLoaded}
	<!-- Skeleton loading state -->
	<div class="animate-pulse">
		<div class="h-12 bg-gray-200 rounded w-3/4 mb-4"></div>
		<div class="h-6 bg-gray-200 rounded w-1/2"></div>
	</div>
{:else}
	<!-- Actual content based on variant -->
	<div data-experiment={EXPERIMENT_KEY} data-variant={variant}>
		<h1 class="text-4xl font-bold text-gray-900 mb-4">
			{content.headline}
		</h1>
		<p class="text-xl text-gray-600">
			{content.subheadline}
		</p>
	</div>
{/if}
