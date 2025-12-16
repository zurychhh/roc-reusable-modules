#!/usr/bin/env npx tsx
/**
 * Setup Experiments - Batch Creation
 *
 * Creates multiple experiments at once.
 * Edit EXPERIMENTS array below with your experiments.
 *
 * Usage:
 *   POSTHOG_PERSONAL_API_KEY=phx_xxx npx tsx scripts/setup-experiments.ts
 */

const POSTHOG_API_HOST = process.env.POSTHOG_API_HOST || 'https://eu.posthog.com';
const POSTHOG_PERSONAL_API_KEY = process.env.POSTHOG_PERSONAL_API_KEY;

if (!POSTHOG_PERSONAL_API_KEY) {
	console.error('Error: POSTHOG_PERSONAL_API_KEY environment variable is required');
	process.exit(1);
}

const headers = {
	'Authorization': `Bearer ${POSTHOG_PERSONAL_API_KEY}`,
	'Content-Type': 'application/json'
};

// ============================================
// CONFIGURE YOUR EXPERIMENTS HERE
// ============================================

interface ExperimentConfig {
	name: string;
	flagKey: string;
	description: string;
	variants: { key: string; rollout_percentage: number }[];
	goalEvent: string;
}

const EXPERIMENTS: ExperimentConfig[] = [
	// Example experiments - customize these:
	{
		name: 'Hero Headline Test',
		flagKey: 'hero-headline-test',
		description: 'Testing different headlines on the hero section',
		variants: [
			{ key: 'control', rollout_percentage: 34 },
			{ key: 'variant_a', rollout_percentage: 33 },
			{ key: 'variant_b', rollout_percentage: 33 }
		],
		goalEvent: 'form_submit'
	},
	{
		name: 'CTA Button Text Test',
		flagKey: 'cta-button-text',
		description: 'Testing different CTA button texts',
		variants: [
			{ key: 'control', rollout_percentage: 50 },
			{ key: 'test', rollout_percentage: 50 }
		],
		goalEvent: 'cta_click'
	},
	{
		name: 'Pricing Layout Test',
		flagKey: 'pricing-layout',
		description: 'Testing different pricing page layouts',
		variants: [
			{ key: 'control', rollout_percentage: 50 },
			{ key: 'test', rollout_percentage: 50 }
		],
		goalEvent: 'pricing_plan_click'
	}
];

// ============================================
// CREATION LOGIC
// ============================================

async function createExperiment(config: ExperimentConfig): Promise<number | null> {
	console.log(`\n📝 Creating: "${config.name}"`);
	console.log(`   Flag: ${config.flagKey}`);

	// 1. Create feature flag
	console.log('   1. Creating feature flag...');
	const flagResponse = await fetch(`${POSTHOG_API_HOST}/api/projects/@current/feature_flags/`, {
		method: 'POST',
		headers,
		body: JSON.stringify({
			key: config.flagKey,
			name: `Flag for ${config.name}`,
			filters: {
				groups: [{ properties: [], rollout_percentage: 100 }],
				multivariate: { variants: config.variants }
			},
			active: true
		})
	});

	if (!flagResponse.ok) {
		const error = await flagResponse.json();
		if (error.detail?.includes('already exists')) {
			console.log('      ⚠️ Flag already exists, continuing...');
		} else {
			console.error('      ❌ Error:', error);
			return null;
		}
	} else {
		const flag = await flagResponse.json();
		console.log(`      ✅ Flag created [${flag.id}]`);
	}

	// 2. Create experiment
	console.log('   2. Creating experiment...');
	const expResponse = await fetch(`${POSTHOG_API_HOST}/api/projects/@current/experiments/`, {
		method: 'POST',
		headers,
		body: JSON.stringify({
			name: config.name,
			description: config.description,
			feature_flag_key: config.flagKey,
			parameters: {
				feature_flag_variants: config.variants
			},
			metrics: [{
				kind: 'ExperimentMetric',
				metric_type: 'funnel',
				series: [{ kind: 'EventsNode', event: config.goalEvent }]
			}]
		})
	});

	if (!expResponse.ok) {
		const error = await expResponse.json();
		console.error('      ❌ Error:', error);
		return null;
	}

	const exp = await expResponse.json();
	console.log(`      ✅ Experiment created [${exp.id}]`);
	return exp.id;
}

async function main() {
	console.log('\n🚀 Setting Up Experiments\n');
	console.log('='.repeat(60));

	const results: { name: string; id: number | null; success: boolean }[] = [];

	for (const config of EXPERIMENTS) {
		const id = await createExperiment(config);
		results.push({
			name: config.name,
			id,
			success: id !== null
		});
	}

	console.log('\n' + '='.repeat(60));
	console.log('\n📊 Summary:\n');

	for (const result of results) {
		const icon = result.success ? '✅' : '❌';
		const idStr = result.id ? ` [${result.id}]` : '';
		console.log(`   ${icon} ${result.name}${idStr}`);
	}

	const successful = results.filter(r => r.success).length;
	console.log(`\n   Total: ${successful}/${results.length} experiments created`);

	if (successful > 0) {
		console.log('\n   To launch an experiment:');
		console.log('   npx tsx scripts/posthog-cli.ts launch <experiment-id>');
	}

	console.log('\n');
}

main().catch(console.error);
