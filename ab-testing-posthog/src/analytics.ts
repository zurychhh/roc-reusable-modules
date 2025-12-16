/**
 * A/B Testing Analytics Utilities
 *
 * Helper functions for tracking experiments and conversions.
 * Can be used alongside PostHog or with GTM/GA4.
 */

// Global type declaration for dataLayer
declare global {
	interface Window {
		dataLayer: Record<string, any>[];
		gtag: (...args: any[]) => void;
	}
}

// ============================================
// DATA LAYER UTILITIES (for GTM/GA4)
// ============================================

/**
 * Initialize dataLayer
 */
export function initDataLayer(): void {
	if (typeof window !== 'undefined') {
		window.dataLayer = window.dataLayer || [];
	}
}

/**
 * Push event to dataLayer
 */
export function pushEvent(eventName: string, eventParams: Record<string, any> = {}): void {
	if (typeof window === 'undefined') return;

	window.dataLayer = window.dataLayer || [];
	window.dataLayer.push({
		event: eventName,
		...eventParams
	});

	// Debug in development
	if (typeof process !== 'undefined' && process.env.NODE_ENV === 'development') {
		console.log('[Analytics] Event:', eventName, eventParams);
	}
}

// ============================================
// A/B TESTING / EXPERIMENT EVENTS
// ============================================

/**
 * Track experiment impression (when user sees variant)
 * Sends to GTM dataLayer for GA4 consistency
 */
export function trackExperimentImpression(data: {
	experimentId: string;
	experimentName: string;
	variantId: string;
	variantName: string;
}): void {
	pushEvent('experiment_impression', {
		event_category: 'A/B Testing',
		experiment_id: data.experimentId,
		experiment_name: data.experimentName,
		variant_id: data.variantId,
		variant_name: data.variantName
	});
}

/**
 * Track conversion in experiment context
 * Allows linking conversion to specific variant
 */
export function trackExperimentConversion(data: {
	experimentId: string;
	variantId: string;
	conversionType: string;
	conversionValue?: number;
	additionalData?: Record<string, unknown>;
}): void {
	pushEvent('experiment_conversion', {
		event_category: 'A/B Testing',
		experiment_id: data.experimentId,
		variant_id: data.variantId,
		conversion_type: data.conversionType,
		conversion_value: data.conversionValue ?? 1,
		...data.additionalData
	});
}

// ============================================
// ACTIVE EXPERIMENTS STORE
// ============================================

/**
 * Store for active experiments per user
 * Useful for passing to backend (API, HubSpot, etc.)
 */
let activeExperiments: Map<string, string> = new Map();

/**
 * Set active experiment variant
 */
export function setActiveExperiment(experimentId: string, variantId: string): void {
	activeExperiments.set(experimentId, variantId);
}

/**
 * Get active experiment variant
 */
export function getActiveExperiment(experimentId: string): string | undefined {
	return activeExperiments.get(experimentId);
}

/**
 * Get all active experiments as object
 * Perfect for sending to backend APIs
 *
 * @example
 * // In API call
 * await createLead({
 *   email: form.email,
 *   experiments: getAllActiveExperiments()
 * });
 */
export function getAllActiveExperiments(): Record<string, string> {
	return Object.fromEntries(activeExperiments);
}

/**
 * Clear all active experiments
 */
export function clearActiveExperiments(): void {
	activeExperiments.clear();
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Format experiments data for CRM (HubSpot, etc.)
 *
 * @example
 * const crmData = formatExperimentsForCRM();
 * // "hero-test:variant_a,pricing-test:control"
 */
export function formatExperimentsForCRM(): string {
	const experiments = getAllActiveExperiments();
	return Object.entries(experiments)
		.map(([key, value]) => `${key}:${value}`)
		.join(',');
}

/**
 * Parse experiments data from CRM string
 */
export function parseExperimentsFromCRM(data: string): Record<string, string> {
	if (!data) return {};

	const result: Record<string, string> = {};
	data.split(',').forEach(pair => {
		const [key, value] = pair.split(':');
		if (key && value) {
			result[key.trim()] = value.trim();
		}
	});
	return result;
}
