/**
 * PostHog A/B Testing & Analytics Integration
 *
 * Framework-agnostic initialization module.
 * Customize imports for your framework (SvelteKit, Next.js, etc.)
 *
 * Documentation: https://posthog.com/docs/libraries/js
 */

import posthog from 'posthog-js';

// Type for experiment variant
export type ExperimentVariant = string | boolean | undefined;

// Experiment configuration interface
export interface ExperimentConfig {
	key: string;
	fallback: string;
}

// Initialization flag
let isInitialized = false;

/**
 * Get environment variable (customize for your framework)
 *
 * Examples:
 * - SvelteKit: import { PUBLIC_POSTHOG_KEY } from '$env/static/public'
 * - Next.js: process.env.NEXT_PUBLIC_POSTHOG_KEY
 * - Vite: import.meta.env.VITE_POSTHOG_KEY
 */
function getEnvVar(key: string): string | undefined {
	// Browser environment
	if (typeof window !== 'undefined') {
		// Check for Vite
		if (typeof import.meta !== 'undefined' && (import.meta as any).env) {
			return (import.meta as any).env[key];
		}
		// Check for Next.js / CRA
		if (typeof process !== 'undefined' && process.env) {
			return process.env[key];
		}
	}
	// Fallback: check global process.env
	if (typeof process !== 'undefined' && process.env) {
		return process.env[key];
	}
	return undefined;
}

/**
 * Configuration interface for PostHog initialization
 */
export interface PostHogConfig {
	apiKey: string;
	apiHost?: string;
	debug?: boolean;
	capturePageview?: boolean;
	capturePageleave?: boolean;
}

/**
 * Initialize PostHog client
 * Call once in your app's root layout/component
 *
 * @param config - Configuration object or uses environment variables if not provided
 *
 * Environment variables (if config not provided):
 * - PUBLIC_POSTHOG_KEY or NEXT_PUBLIC_POSTHOG_KEY or VITE_POSTHOG_KEY
 * - PUBLIC_POSTHOG_HOST or NEXT_PUBLIC_POSTHOG_HOST or VITE_POSTHOG_HOST
 */
export function initPostHog(config?: Partial<PostHogConfig>): void {
	// Only run in browser
	if (typeof window === 'undefined') return;
	if (isInitialized) return;

	const apiKey = config?.apiKey
		|| getEnvVar('PUBLIC_POSTHOG_KEY')
		|| getEnvVar('NEXT_PUBLIC_POSTHOG_KEY')
		|| getEnvVar('VITE_POSTHOG_KEY');

	const apiHost = config?.apiHost
		|| getEnvVar('PUBLIC_POSTHOG_HOST')
		|| getEnvVar('NEXT_PUBLIC_POSTHOG_HOST')
		|| getEnvVar('VITE_POSTHOG_HOST')
		|| 'https://eu.posthog.com';

	console.log('[PostHog] Initializing with key:', apiKey?.substring(0, 10) + '...');
	console.log('[PostHog] API Host:', apiHost);

	if (!apiKey || apiKey.includes('YOUR_PROJECT_API_KEY')) {
		console.warn('[PostHog] No API key provided. A/B tests will not work.');
		return;
	}

	try {
		posthog.init(apiKey, {
			api_host: apiHost,
			capture_pageview: config?.capturePageview ?? true,
			capture_pageleave: config?.capturePageleave ?? true,
			debug: config?.debug ?? false,
			loaded: (ph) => {
				console.log('[PostHog] Loaded! Distinct ID:', ph.get_distinct_id());
			}
		});

		isInitialized = true;
		console.log('[PostHog] Initialized successfully');
	} catch (error) {
		console.error('[PostHog] Initialization error:', error);
	}
}

/**
 * Get experiment variant
 *
 * @param flagKey - Feature flag key in PostHog
 * @param fallback - Default value if flag doesn't exist
 * @returns Experiment variant
 *
 * @example
 * const variant = getVariant('hero-headline-test', 'control')
 * // variant: 'control' | 'variant_a' | 'variant_b'
 */
export function getVariant(flagKey: string, fallback: string): string {
	if (typeof window === 'undefined' || !isInitialized) return fallback;

	try {
		const variant = posthog.getFeatureFlag(flagKey);
		return (variant as string) ?? fallback;
	} catch {
		return fallback;
	}
}

/**
 * Get feature flag payload (for complex configurations)
 *
 * @example
 * const config = getVariantPayload('pricing-test', { order: ['start', 'eco', 'pro'] })
 * // config: { order: ['eco', 'start', 'pro'], highlight: 'eco' }
 */
export function getVariantPayload<T>(flagKey: string, fallback: T): T {
	if (typeof window === 'undefined' || !isInitialized) return fallback;

	try {
		const payload = posthog.getFeatureFlagPayload(flagKey);
		return (payload as T) ?? fallback;
	} catch {
		return fallback;
	}
}

/**
 * Check if feature flag is enabled (boolean)
 */
export function isFeatureEnabled(flagKey: string): boolean {
	if (typeof window === 'undefined' || !isInitialized) return false;

	try {
		return posthog.isFeatureEnabled(flagKey) ?? false;
	} catch {
		return false;
	}
}

/**
 * Track conversion event for experiment
 *
 * @example
 * trackExperimentConversion('hero-headline-test', 'form_submit', { plan: 'pro' })
 */
export function trackExperimentConversion(
	experimentKey: string,
	eventName: string,
	properties?: Record<string, unknown>
): void {
	if (typeof window === 'undefined' || !isInitialized) return;

	try {
		posthog.capture(eventName, {
			$experiment_key: experimentKey,
			...properties
		});
	} catch (error) {
		console.error('[PostHog] Tracking error:', error);
	}
}

/**
 * Track experiment exposure (when user sees variant)
 * PostHog does this automatically, but can be called manually
 */
export function trackExperimentExposure(experimentKey: string, variant: string): void {
	if (typeof window === 'undefined' || !isInitialized) return;

	try {
		posthog.capture('$experiment_started', {
			$experiment_key: experimentKey,
			$experiment_variant: variant
		});
	} catch (error) {
		console.error('[PostHog] Exposure tracking error:', error);
	}
}

/**
 * Identify user (after login/registration)
 */
export function identifyUser(
	userId: string,
	properties?: Record<string, unknown>
): void {
	if (typeof window === 'undefined' || !isInitialized) return;

	try {
		posthog.identify(userId, properties);
	} catch (error) {
		console.error('[PostHog] Identify error:', error);
	}
}

/**
 * Reset user (after logout)
 */
export function resetUser(): void {
	if (typeof window === 'undefined' || !isInitialized) return;

	try {
		posthog.reset();
	} catch (error) {
		console.error('[PostHog] Reset error:', error);
	}
}

/**
 * Set user properties
 */
export function setUserProperties(properties: Record<string, unknown>): void {
	if (typeof window === 'undefined' || !isInitialized) return;

	try {
		posthog.people.set(properties);
	} catch (error) {
		console.error('[PostHog] Set properties error:', error);
	}
}

/**
 * Get current user's distinctId
 */
export function getDistinctId(): string | undefined {
	if (typeof window === 'undefined' || !isInitialized) return undefined;

	try {
		return posthog.get_distinct_id();
	} catch {
		return undefined;
	}
}

/**
 * Get all active experiments' variants
 * Useful for debugging
 */
export function getAllActiveExperiments(): Record<string, string | boolean> {
	if (typeof window === 'undefined' || !isInitialized) return {};

	try {
		return posthog.featureFlags.getFlagVariants() ?? {};
	} catch {
		return {};
	}
}

/**
 * Force refresh feature flags from server
 */
export async function reloadFeatureFlags(): Promise<void> {
	if (typeof window === 'undefined' || !isInitialized) return;

	try {
		await posthog.reloadFeatureFlags();
	} catch (error) {
		console.error('[PostHog] Reload flags error:', error);
	}
}

/**
 * Check if PostHog is initialized
 */
export function isPostHogReady(): boolean {
	return typeof window !== 'undefined' && isInitialized;
}

/**
 * Register callback when feature flags are loaded
 *
 * @example
 * onFeatureFlags((flags) => {
 *   console.log('Flags loaded:', flags);
 *   const variant = getVariant('my-test', 'control');
 * });
 */
export function onFeatureFlags(callback: () => void): void {
	if (typeof window === 'undefined') return;

	if (!isInitialized) {
		console.warn('[PostHog] Not initialized. Callback will be called when initialized.');
	}

	posthog.onFeatureFlags(callback);
}

// Export instance for advanced use cases
export { posthog };
