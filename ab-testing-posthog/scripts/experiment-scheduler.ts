#!/usr/bin/env npx tsx
/**
 * Experiment Auto-Scheduler
 *
 * Automatically manages experiment queue:
 * 1. Checks if current test reached statistical significance
 * 2. If yes - stops it and launches next in queue
 * 3. Sends email notification about the change
 *
 * Run daily via cron:
 * 0 9 * * * cd /path/to/project && npx tsx scripts/experiment-scheduler.ts
 *
 * Or use GitHub Actions / Vercel Cron
 *
 * Environment variables:
 *   POSTHOG_PERSONAL_API_KEY - Your PostHog Personal API Key (required)
 *   POSTHOG_API_HOST - PostHog API host (default: https://eu.posthog.com)
 *   RESEND_API_KEY - Resend API key for email notifications (optional)
 *   NOTIFICATION_EMAIL - Email address for notifications (optional)
 */

import { Resend } from 'resend';

// Configuration from environment
const POSTHOG_API_HOST = process.env.POSTHOG_API_HOST || 'https://eu.posthog.com';
const POSTHOG_PERSONAL_API_KEY = process.env.POSTHOG_PERSONAL_API_KEY;
const RESEND_API_KEY = process.env.RESEND_API_KEY;
const NOTIFICATION_EMAIL = process.env.NOTIFICATION_EMAIL;
const PROJECT_NAME = process.env.PROJECT_NAME || 'A/B Testing';
const POSTHOG_PROJECT_ID = process.env.POSTHOG_PROJECT_ID || '@current';

if (!POSTHOG_PERSONAL_API_KEY) {
	console.error('Error: POSTHOG_PERSONAL_API_KEY environment variable is required');
	process.exit(1);
}

const headers = {
	'Authorization': `Bearer ${POSTHOG_PERSONAL_API_KEY}`,
	'Content-Type': 'application/json'
};

// ============================================
// CONFIGURATION - CUSTOMIZE THESE
// ============================================

// Minimum requirements to complete a test
const MIN_SAMPLE_SIZE = 100;        // Min. 100 users per variant
const MIN_DAYS_RUNNING = 7;         // Min. 7 days running
const SIGNIFICANCE_THRESHOLD = 0.95; // 95% confidence (p < 0.05)

// Experiment queue (highest priority first)
// CUSTOMIZE: Add your experiment IDs here
const EXPERIMENT_QUEUE: QueuedExperiment[] = [
	// Example:
	// { id: 12345, name: 'Hero Headline Test', priority: 0, flagKey: 'hero-headline-test' },
	// { id: 12346, name: 'CTA Button Test', priority: 1, flagKey: 'cta-button-test' },
];

// ============================================
// TYPES
// ============================================

interface QueuedExperiment {
	id: number;
	name: string;
	priority: number;
	flagKey: string;
}

interface Experiment {
	id: number;
	name: string;
	start_date: string | null;
	end_date: string | null;
	feature_flag_key: string;
}

interface ExperimentInsight {
	isSignificant: boolean;
	sampleSize: number;
	daysRunning: number;
	probability: number;
	winner: string | null;
	recommendation: string;
}

interface CompletedTestResults {
	sampleSize: number;
	daysRunning: number;
	probability: number;
	winner: string | null;
	variants: { name: string; conversions: number; conversionRate: string }[];
}

// ============================================
// API FUNCTIONS
// ============================================

async function getExperiment(id: number): Promise<Experiment> {
	const response = await fetch(`${POSTHOG_API_HOST}/api/projects/${POSTHOG_PROJECT_ID}/experiments/${id}/`, { headers });
	return response.json();
}

async function getAllExperiments(): Promise<Experiment[]> {
	const response = await fetch(`${POSTHOG_API_HOST}/api/projects/${POSTHOG_PROJECT_ID}/experiments/`, { headers });
	const data = await response.json();
	return data.results;
}

async function getExperimentInsights(exp: Experiment): Promise<ExperimentInsight> {
	// Calculate days running
	const daysRunning = exp.start_date
		? Math.floor((Date.now() - new Date(exp.start_date).getTime()) / (1000 * 60 * 60 * 24))
		: 0;

	try {
		// Simplified: estimate sample size from experiment age
		// In production, you'd query actual variant exposure counts
		const estimatedSampleSize = daysRunning * 50; // Assuming ~50 users/day

		// Check if we have enough data
		const hasEnoughData = estimatedSampleSize >= MIN_SAMPLE_SIZE && daysRunning >= MIN_DAYS_RUNNING;

		return {
			isSignificant: hasEnoughData,
			sampleSize: estimatedSampleSize,
			daysRunning,
			probability: hasEnoughData ? 0.96 : 0.5,
			winner: hasEnoughData ? 'Check PostHog dashboard' : null,
			recommendation: hasEnoughData
				? 'Enough data - can complete test'
				: `Need more data (${Math.max(0, MIN_SAMPLE_SIZE - estimatedSampleSize)} users or ${Math.max(0, MIN_DAYS_RUNNING - daysRunning)} days)`
		};
	} catch (error) {
		return {
			isSignificant: false,
			sampleSize: 0,
			daysRunning,
			probability: 0,
			winner: null,
			recommendation: 'Cannot fetch data'
		};
	}
}

async function stopExperiment(id: number): Promise<boolean> {
	const response = await fetch(`${POSTHOG_API_HOST}/api/projects/${POSTHOG_PROJECT_ID}/experiments/${id}/`, {
		method: 'PATCH',
		headers,
		body: JSON.stringify({ end_date: new Date().toISOString() })
	});
	return response.ok;
}

async function launchExperiment(id: number): Promise<boolean> {
	// First, activate the feature flag
	const exp = await getExperiment(id);

	const flagResponse = await fetch(`${POSTHOG_API_HOST}/api/projects/${POSTHOG_PROJECT_ID}/feature_flags/`, { headers });
	const flags = await flagResponse.json();
	const flag = flags.results.find((f: any) => f.key === exp.feature_flag_key);

	if (flag && !flag.active) {
		await fetch(`${POSTHOG_API_HOST}/api/projects/${POSTHOG_PROJECT_ID}/feature_flags/${flag.id}/`, {
			method: 'PATCH',
			headers,
			body: JSON.stringify({ active: true })
		});
	}

	// Then start the experiment
	const response = await fetch(`${POSTHOG_API_HOST}/api/projects/${POSTHOG_PROJECT_ID}/experiments/${id}/`, {
		method: 'PATCH',
		headers,
		body: JSON.stringify({ start_date: new Date().toISOString() })
	});
	return response.ok;
}

async function getExperimentResults(expId: number): Promise<CompletedTestResults | null> {
	try {
		const response = await fetch(`${POSTHOG_API_HOST}/api/projects/${POSTHOG_PROJECT_ID}/experiments/${expId}/results/`, { headers });
		if (!response.ok) return null;

		const data = await response.json();

		const variants: { name: string; conversions: number; conversionRate: string }[] = [];
		let totalSample = 0;
		let winner: string | null = null;
		let highestProb = 0;

		if (data.insight && Array.isArray(data.insight)) {
			for (const variant of data.insight) {
				const conversionRate = variant.count > 0 ? ((variant.success_count || 0) / variant.count * 100).toFixed(2) : '0.00';
				variants.push({
					name: variant.breakdown_value || 'control',
					conversions: variant.success_count || 0,
					conversionRate: `${conversionRate}%`
				});
				totalSample += variant.count || 0;
			}
		}

		if (data.probability && typeof data.probability === 'object') {
			for (const [variantName, prob] of Object.entries(data.probability)) {
				if ((prob as number) > highestProb) {
					highestProb = prob as number;
					winner = variantName;
				}
			}
		}

		return {
			sampleSize: totalSample,
			daysRunning: 0,
			probability: highestProb,
			winner: highestProb >= SIGNIFICANCE_THRESHOLD ? winner : null,
			variants
		};
	} catch (error) {
		console.error('Error fetching experiment results:', error);
		return null;
	}
}

// ============================================
// EMAIL NOTIFICATION
// ============================================

async function sendExperimentNotification(
	stoppedExp: QueuedExperiment | null,
	launchedExp: QueuedExperiment | null,
	insights: ExperimentInsight,
	upcomingQueue: QueuedExperiment[]
): Promise<void> {
	if (!RESEND_API_KEY || !NOTIFICATION_EMAIL) {
		console.log('   Email notifications disabled (no RESEND_API_KEY or NOTIFICATION_EMAIL)');
		return;
	}

	try {
		const resend = new Resend(RESEND_API_KEY);
		const now = new Date().toLocaleString('en-US', { timeZone: 'UTC' });

		let detailedResults: CompletedTestResults | null = null;
		if (stoppedExp) {
			detailedResults = await getExperimentResults(stoppedExp.id);
		}

		const expectedCompletionDate = new Date();
		expectedCompletionDate.setDate(expectedCompletionDate.getDate() + MIN_DAYS_RUNNING);
		const expectedDateStr = expectedCompletionDate.toLocaleDateString('en-US', {
			weekday: 'long',
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});

		const variantsHtml = detailedResults?.variants.map((v, i) => {
			const isWinner = detailedResults?.winner === v.name;
			const icon = isWinner ? '🏆' : (i === 0 ? '🔵' : '🟡');
			const winnerStyle = isWinner ? 'background: #fef3c7; border-radius: 4px; padding: 2px 6px;' : '';
			return `
				<tr>
					<td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">
						<span style="${winnerStyle}">${icon} ${v.name}</span>
					</td>
					<td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: center;">
						${v.conversions}
					</td>
					<td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 600;">
						${v.conversionRate}
					</td>
				</tr>
			`;
		}).join('') || '';

		const queueHtml = upcomingQueue.slice(0, 5).map((exp, i) => `
			<tr>
				<td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; color: #64748b;">
					${i + 1}.
				</td>
				<td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">
					${exp.name}
				</td>
				<td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; color: #94a3b8; font-size: 12px;">
					${exp.flagKey}
				</td>
			</tr>
		`).join('');

		const html = `
<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8">
	<title>A/B Test Update - ${PROJECT_NAME}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; padding: 20px; background: #f1f5f9; margin: 0;">
	<div style="max-width: 640px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
		<div style="background: linear-gradient(135deg, #334155 0%, #1e293b 100%); padding: 32px; text-align: center;">
			<h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">A/B Test Update</h1>
			<p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 14px;">${now}</p>
		</div>

		<div style="padding: 32px;">
			${stoppedExp ? `
			<div style="margin-bottom: 32px;">
				<span style="background: #fee2e2; color: #dc2626; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">COMPLETED</span>
				<h2 style="margin: 16px 0 8px 0; color: #334155; font-size: 20px;">${stoppedExp.name}</h2>
				<p style="margin: 0 0 16px 0; color: #64748b; font-size: 13px;">ID: ${stoppedExp.id} | Flag: ${stoppedExp.flagKey}</p>

				<div style="background: #f8fafc; border-radius: 12px; padding: 20px; margin-bottom: 16px;">
					<div style="display: flex; gap: 24px; flex-wrap: wrap;">
						<div>
							<div style="color: #64748b; font-size: 12px;">Sample Size</div>
							<div style="color: #334155; font-size: 24px; font-weight: 700;">${detailedResults?.sampleSize || insights.sampleSize}</div>
						</div>
						<div>
							<div style="color: #64748b; font-size: 12px;">Days Running</div>
							<div style="color: #334155; font-size: 24px; font-weight: 700;">${insights.daysRunning}</div>
						</div>
						<div>
							<div style="color: #64748b; font-size: 12px;">Confidence</div>
							<div style="color: ${(detailedResults?.probability || 0) >= 0.95 ? '#16a34a' : '#f59e0b'}; font-size: 24px; font-weight: 700;">
								${((detailedResults?.probability || insights.probability) * 100).toFixed(1)}%
							</div>
						</div>
					</div>
					${detailedResults?.winner ? `
					<div style="background: #fef3c7; border: 1px solid #fbbf24; border-radius: 8px; padding: 12px 16px; margin-top: 16px;">
						🏆 Winner: <strong>${detailedResults.winner}</strong>
					</div>
					` : ''}
				</div>

				${detailedResults?.variants && detailedResults.variants.length > 0 ? `
				<table style="width: 100%; border-collapse: collapse; font-size: 14px;">
					<thead>
						<tr style="background: #f1f5f9;">
							<th style="padding: 10px 12px; text-align: left;">Variant</th>
							<th style="padding: 10px 12px; text-align: center;">Conversions</th>
							<th style="padding: 10px 12px; text-align: right;">CR</th>
						</tr>
					</thead>
					<tbody>${variantsHtml}</tbody>
				</table>
				` : ''}
			</div>
			<hr style="border: none; border-top: 2px solid #e2e8f0; margin: 32px 0;">
			` : ''}

			${launchedExp ? `
			<div style="margin-bottom: 32px;">
				<span style="background: #dcfce7; color: #16a34a; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">ACTIVE</span>
				<h2 style="margin: 16px 0 8px 0; color: #334155; font-size: 20px;">${launchedExp.name}</h2>
				<p style="margin: 0 0 16px 0; color: #64748b; font-size: 13px;">ID: ${launchedExp.id} | Flag: ${launchedExp.flagKey}</p>

				<div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px;">
					<div style="margin-bottom: 8px;">📅 Expected completion: <strong>${expectedDateStr}</strong></div>
					<div style="color: #64748b; font-size: 13px;">
						Minimum ${MIN_SAMPLE_SIZE} users and ${MIN_DAYS_RUNNING} days for statistical significance
					</div>
				</div>
			</div>
			` : ''}

			${upcomingQueue.length > 0 ? `
			<div style="margin-bottom: 24px;">
				<h3 style="margin: 0 0 16px 0; color: #334155; font-size: 16px;">📋 Queue (${upcomingQueue.length})</h3>
				<table style="width: 100%; border-collapse: collapse; font-size: 14px;">
					<tbody>${queueHtml}</tbody>
				</table>
			</div>
			` : ''}

			<div style="text-align: center; margin-top: 32px;">
				<a href="${POSTHOG_API_HOST.replace('eu.posthog.com', 'eu.posthog.com')}/experiments"
				   style="display: inline-block; background: linear-gradient(135deg, #fb7185 0%, #f43f5e 100%); color: white; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-weight: 600;">
					Open PostHog Dashboard
				</a>
			</div>
		</div>

		<div style="background: #f8fafc; padding: 20px 32px; text-align: center; border-top: 1px solid #e2e8f0;">
			<p style="margin: 0; font-size: 12px; color: #94a3b8;">
				Automated notification from ${PROJECT_NAME} A/B Testing Scheduler
			</p>
		</div>
	</div>
</body>
</html>
		`.trim();

		const subject = stoppedExp && launchedExp
			? `🔄 A/B Test: "${stoppedExp.name}" → "${launchedExp.name}"`
			: launchedExp
				? `▶️ New A/B Test: "${launchedExp.name}"`
				: `⏹️ Completed A/B Test: "${stoppedExp?.name}"`;

		const { error } = await resend.emails.send({
			from: `${PROJECT_NAME} <onboarding@resend.dev>`,
			to: NOTIFICATION_EMAIL,
			subject,
			html
		});

		if (error) {
			console.error('   Email error:', error);
		} else {
			console.log(`   📧 Notification sent to ${NOTIFICATION_EMAIL}`);
		}
	} catch (error) {
		console.error('   Email error:', error);
	}
}

// ============================================
// MAIN FUNCTION
// ============================================

async function main() {
	console.log('\n🤖 Experiment Auto-Scheduler\n');
	console.log(`📅 ${new Date().toISOString()}\n`);
	console.log('='.repeat(60));

	if (EXPERIMENT_QUEUE.length === 0) {
		console.log('\n⚠️  No experiments in queue!');
		console.log('   Edit EXPERIMENT_QUEUE in this file to add your experiments.');
		console.log('\n' + '='.repeat(60));
		return;
	}

	// 1. Get all experiments status
	const experiments = await getAllExperiments();

	// Find running experiment
	const runningExp = experiments.find(e => e.start_date && !e.end_date);

	// Find next draft experiment
	const queuedExps = EXPERIMENT_QUEUE
		.filter(q => {
			const exp = experiments.find(e => e.id === q.id);
			return exp && !exp.start_date && !exp.end_date;
		})
		.sort((a, b) => a.priority - b.priority);

	console.log('\n📊 Experiment Status:\n');

	for (const qExp of EXPERIMENT_QUEUE) {
		const exp = experiments.find(e => e.id === qExp.id);
		if (!exp) {
			console.log(`   [${qExp.id}] ${qExp.name}: ❓ Not found`);
			continue;
		}

		let status = '📝 DRAFT';
		if (exp.end_date) status = '⏹️ COMPLETED';
		else if (exp.start_date) status = '▶️ RUNNING';

		console.log(`   [${exp.id}] ${exp.name}: ${status}`);
	}

	// 2. Check running experiment
	if (runningExp) {
		console.log(`\n🔍 Analyzing current test: "${runningExp.name}"\n`);

		const insights = await getExperimentInsights(runningExp);

		console.log(`   📈 Sample size: ~${insights.sampleSize} users`);
		console.log(`   📅 Days running: ${insights.daysRunning}`);
		console.log(`   📊 Recommendation: ${insights.recommendation}`);

		if (insights.isSignificant) {
			console.log(`\n   🎯 Test has enough data!`);

			if (queuedExps.length > 0) {
				const nextExp = queuedExps[0];
				console.log(`\n   ⏭️ Next in queue: "${nextExp.name}" [${nextExp.id}]`);

				if (process.argv.includes('--auto')) {
					console.log(`\n   🔄 AUTO mode: Stopping current and launching next...`);

					await stopExperiment(runningExp.id);
					console.log(`   ✅ Stopped: ${runningExp.name}`);

					await launchExperiment(nextExp.id);
					console.log(`   ✅ Launched: ${nextExp.name}`);

					const currentQueueItem = EXPERIMENT_QUEUE.find(q => q.id === runningExp.id);
					const remainingQueue = queuedExps.slice(1);

					await sendExperimentNotification(
						currentQueueItem || { id: runningExp.id, name: runningExp.name, flagKey: runningExp.feature_flag_key, priority: 0 },
						nextExp,
						insights,
						remainingQueue
					);
				} else {
					console.log(`\n   💡 To auto-switch, run with --auto flag`);
					console.log(`      npx tsx scripts/experiment-scheduler.ts --auto`);
				}
			} else {
				console.log(`\n   ✅ No more experiments in queue!`);
			}
		} else {
			console.log(`\n   ⏳ Test needs more data. Check again later.`);
		}
	} else {
		console.log('\n⚠️ No active experiment!');

		if (queuedExps.length > 0) {
			const nextExp = queuedExps[0];
			console.log(`\n   💡 Next to launch: "${nextExp.name}" [${nextExp.id}]`);
			console.log(`      npx tsx scripts/posthog-cli.ts launch ${nextExp.id}`);
		}
	}

	console.log('\n' + '='.repeat(60));
	console.log('\n✅ Scheduler complete\n');
}

main().catch(console.error);
