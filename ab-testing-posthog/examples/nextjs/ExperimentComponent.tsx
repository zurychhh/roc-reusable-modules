'use client';

/**
 * Example A/B Test Component for Next.js
 *
 * This component demonstrates how to implement an A/B test
 * with PostHog feature flags in React/Next.js.
 */

import { useState, useEffect } from 'react';
import posthog from 'posthog-js';
import { setActiveExperiment, trackExperimentImpression } from '@/lib/analytics';

// Experiment configuration
const EXPERIMENT_KEY = 'hero-headline-test';

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

type VariantKey = keyof typeof variants;

export default function ExperimentComponent() {
	const [variant, setVariant] = useState<VariantKey>('control');
	const [isLoaded, setIsLoaded] = useState(false);

	useEffect(() => {
		// Timeout fallback - show control after 1.5s if PostHog doesn't load
		const timeout = setTimeout(() => {
			if (!isLoaded) {
				setIsLoaded(true);
				console.log('[A/B Test] Fallback to control (timeout)');
			}
		}, 1500);

		// Wait for PostHog feature flags
		posthog.onFeatureFlags(() => {
			clearTimeout(timeout);

			// Get assigned variant
			const flag = posthog.getFeatureFlag(EXPERIMENT_KEY);
			const assignedVariant = (flag as VariantKey) || 'control';
			setVariant(assignedVariant);
			setIsLoaded(true);

			console.log(`[A/B Test] ${EXPERIMENT_KEY} = ${assignedVariant}`);

			// Track impression
			posthog.capture('$experiment_started', {
				experiment: EXPERIMENT_KEY,
				variant: assignedVariant
			});

			// Track in GTM dataLayer
			trackExperimentImpression({
				experimentId: EXPERIMENT_KEY,
				experimentName: 'Hero Headline Test',
				variantId: assignedVariant,
				variantName: assignedVariant
			});

			// Store for backend/CRM
			setActiveExperiment(EXPERIMENT_KEY, assignedVariant);
		});

		return () => clearTimeout(timeout);
	}, [isLoaded]);

	const content = variants[variant];

	if (!isLoaded) {
		// Skeleton loading state
		return (
			<div className="animate-pulse">
				<div className="h-12 bg-gray-200 rounded w-3/4 mb-4"></div>
				<div className="h-6 bg-gray-200 rounded w-1/2"></div>
			</div>
		);
	}

	return (
		<div data-experiment={EXPERIMENT_KEY} data-variant={variant}>
			<h1 className="text-4xl font-bold text-gray-900 mb-4">
				{content.headline}
			</h1>
			<p className="text-xl text-gray-600">
				{content.subheadline}
			</p>
		</div>
	);
}
