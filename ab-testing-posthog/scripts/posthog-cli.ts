#!/usr/bin/env npx tsx
/**
 * PostHog CLI - A/B Test Management
 *
 * Usage:
 *   npx tsx scripts/posthog-cli.ts list                    # List experiments
 *   npx tsx scripts/posthog-cli.ts create <name> <flag>    # Create experiment
 *   npx tsx scripts/posthog-cli.ts launch <id>             # Launch experiment
 *   npx tsx scripts/posthog-cli.ts stop <id>               # Stop experiment
 *   npx tsx scripts/posthog-cli.ts flags                   # List feature flags
 *
 * Environment variables:
 *   POSTHOG_PERSONAL_API_KEY - Your PostHog Personal API Key
 *   POSTHOG_API_HOST - PostHog API host (default: https://eu.posthog.com)
 */

// Configuration - use environment variables
const POSTHOG_API_HOST = process.env.POSTHOG_API_HOST || 'https://eu.posthog.com';
const POSTHOG_PERSONAL_API_KEY = process.env.POSTHOG_PERSONAL_API_KEY;

if (!POSTHOG_PERSONAL_API_KEY) {
	console.error('Error: POSTHOG_PERSONAL_API_KEY environment variable is required');
	console.error('Get your key at: PostHog Settings -> User -> Personal API Keys');
	process.exit(1);
}

const headers = {
	'Authorization': `Bearer ${POSTHOG_PERSONAL_API_KEY}`,
	'Content-Type': 'application/json'
};

async function listExperiments() {
	console.log('\n A/B Experiments:\n');
	const response = await fetch(`${POSTHOG_API_HOST}/api/projects/@current/experiments/`, { headers });
	const data = await response.json();

	if (data.count === 0) {
		console.log('   No experiments found');
		return;
	}

	for (const exp of data.results) {
		const status = exp.end_date ? ' STOPPED' : exp.start_date ? ' RUNNING' : ' DRAFT';
		const variants = exp.parameters?.feature_flag_variants?.map((v: any) => `${v.key}:${v.rollout_percentage}%`).join(', ');
		console.log(`   [${exp.id}] ${exp.name}`);
		console.log(`       Status: ${status}`);
		console.log(`       Flag: ${exp.feature_flag_key}`);
		console.log(`       Variants: ${variants}`);
		console.log('');
	}
}

async function listFlags() {
	console.log('\n Feature Flags:\n');
	const response = await fetch(`${POSTHOG_API_HOST}/api/projects/@current/feature_flags/`, { headers });
	const data = await response.json();

	for (const flag of data.results) {
		const status = flag.active ? ' active' : ' inactive';
		const variants = flag.filters?.multivariate?.variants?.map((v: any) => `${v.key}:${v.rollout_percentage}%`).join(', ') || 'boolean';
		console.log(`   [${flag.id}] ${flag.key} (${status})`);
		console.log(`       Variants: ${variants}`);
		console.log('');
	}
}

async function createExperiment(name: string, flagKey: string) {
	console.log(`\n Creating experiment "${name}"...\n`);

	// Default variants: control 50%, test 50%
	const variants = [
		{ key: 'control', rollout_percentage: 50 },
		{ key: 'test', rollout_percentage: 50 }
	];

	// 1. Create feature flag
	console.log('   1. Creating feature flag...');
	const flagResponse = await fetch(`${POSTHOG_API_HOST}/api/projects/@current/feature_flags/`, {
		method: 'POST',
		headers,
		body: JSON.stringify({
			key: flagKey,
			name: `Feature Flag for ${name}`,
			filters: {
				groups: [{ properties: [], rollout_percentage: 100 }],
				multivariate: { variants }
			},
			active: true
		})
	});

	if (!flagResponse.ok) {
		const error = await flagResponse.json();
		console.error('    Error creating flag:', error);
		return;
	}
	const flag = await flagResponse.json();
	console.log(`    Feature flag created: ${flag.key} [${flag.id}]`);

	// 2. Create experiment
	console.log('   2. Creating experiment...');
	const expResponse = await fetch(`${POSTHOG_API_HOST}/api/projects/@current/experiments/`, {
		method: 'POST',
		headers,
		body: JSON.stringify({
			name,
			description: `A/B Test: ${name}`,
			feature_flag_key: flagKey,
			parameters: {
				feature_flag_variants: variants
			},
			metrics: [{
				kind: 'ExperimentMetric',
				metric_type: 'funnel',
				series: [{ kind: 'EventsNode', event: '$pageview' }]
			}]
		})
	});

	if (!expResponse.ok) {
		const error = await expResponse.json();
		console.error('    Error creating experiment:', error);
		return;
	}
	const exp = await expResponse.json();
	console.log(`    Experiment created: ${exp.name} [${exp.id}]`);
	console.log(`\n   To launch: npx tsx scripts/posthog-cli.ts launch ${exp.id}`);
}

async function launchExperiment(id: number) {
	console.log(`\n Launching experiment ${id}...\n`);

	const response = await fetch(`${POSTHOG_API_HOST}/api/projects/@current/experiments/${id}/`, {
		method: 'PATCH',
		headers,
		body: JSON.stringify({
			start_date: new Date().toISOString()
		})
	});

	if (!response.ok) {
		const error = await response.json();
		console.error('    Error:', error);
		return;
	}

	const exp = await response.json();
	console.log(`    Experiment "${exp.name}" launched!`);
}

async function stopExperiment(id: number) {
	console.log(`\n Stopping experiment ${id}...\n`);

	const response = await fetch(`${POSTHOG_API_HOST}/api/projects/@current/experiments/${id}/`, {
		method: 'PATCH',
		headers,
		body: JSON.stringify({
			end_date: new Date().toISOString()
		})
	});

	if (!response.ok) {
		const error = await response.json();
		console.error('    Error:', error);
		return;
	}

	const exp = await response.json();
	console.log(`    Experiment "${exp.name}" stopped!`);
}

async function getExperimentResults(id: number) {
	console.log(`\n Getting results for experiment ${id}...\n`);

	const response = await fetch(`${POSTHOG_API_HOST}/api/projects/@current/experiments/${id}/results/`, { headers });

	if (!response.ok) {
		console.error('    Error fetching results');
		return;
	}

	const data = await response.json();
	console.log('   Results:', JSON.stringify(data, null, 2));
}

// CLI
const [,, command, ...args] = process.argv;

switch (command) {
	case 'list':
		listExperiments();
		break;
	case 'flags':
		listFlags();
		break;
	case 'create':
		if (args.length < 2) {
			console.log('Usage: npx tsx scripts/posthog-cli.ts create <name> <flag-key>');
			console.log('Example: npx tsx scripts/posthog-cli.ts create "CTA Button Test" cta-button-test');
		} else {
			createExperiment(args[0], args[1]);
		}
		break;
	case 'launch':
		if (!args[0]) {
			console.log('Usage: npx tsx scripts/posthog-cli.ts launch <experiment-id>');
		} else {
			launchExperiment(parseInt(args[0]));
		}
		break;
	case 'stop':
		if (!args[0]) {
			console.log('Usage: npx tsx scripts/posthog-cli.ts stop <experiment-id>');
		} else {
			stopExperiment(parseInt(args[0]));
		}
		break;
	case 'results':
		if (!args[0]) {
			console.log('Usage: npx tsx scripts/posthog-cli.ts results <experiment-id>');
		} else {
			getExperimentResults(parseInt(args[0]));
		}
		break;
	default:
		console.log(`
PostHog CLI - A/B Test Management

Commands:
  list                    List all experiments
  flags                   List all feature flags
  create <name> <flag>    Create new experiment (50/50 control/test)
  launch <id>             Launch experiment
  stop <id>               Stop experiment
  results <id>            Get experiment results

Environment Variables:
  POSTHOG_PERSONAL_API_KEY  Required - Your PostHog Personal API Key
  POSTHOG_API_HOST          Optional - API host (default: https://eu.posthog.com)

Examples:
  POSTHOG_PERSONAL_API_KEY=phx_xxx npx tsx scripts/posthog-cli.ts list
  npx tsx scripts/posthog-cli.ts create "Pricing Test" pricing-layout-test
  npx tsx scripts/posthog-cli.ts launch 71574
`);
}
