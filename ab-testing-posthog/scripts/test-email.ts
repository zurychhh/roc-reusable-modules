#!/usr/bin/env npx tsx
/**
 * Test Email Notification
 *
 * Sends a test email to verify Resend configuration.
 *
 * Usage:
 *   RESEND_API_KEY=re_xxx NOTIFICATION_EMAIL=your@email.com npx tsx scripts/test-email.ts
 */

import { Resend } from 'resend';

const RESEND_API_KEY = process.env.RESEND_API_KEY;
const NOTIFICATION_EMAIL = process.env.NOTIFICATION_EMAIL;
const PROJECT_NAME = process.env.PROJECT_NAME || 'A/B Testing';

if (!RESEND_API_KEY) {
	console.error('Error: RESEND_API_KEY environment variable is required');
	process.exit(1);
}

if (!NOTIFICATION_EMAIL) {
	console.error('Error: NOTIFICATION_EMAIL environment variable is required');
	process.exit(1);
}

async function main() {
	console.log('\n📧 Testing Email Notification\n');
	console.log(`   Sending to: ${NOTIFICATION_EMAIL}`);

	const resend = new Resend(RESEND_API_KEY);

	const html = `
<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8">
	<title>Test Email - ${PROJECT_NAME}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; padding: 20px; background: #f1f5f9; margin: 0;">
	<div style="max-width: 640px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
		<div style="background: linear-gradient(135deg, #334155 0%, #1e293b 100%); padding: 32px; text-align: center;">
			<h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">Test Email</h1>
			<p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 14px;">${new Date().toISOString()}</p>
		</div>

		<div style="padding: 32px;">
			<div style="background: #dcfce7; border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px; text-align: center;">
				<span style="font-size: 48px;">✅</span>
				<h2 style="color: #16a34a; margin: 16px 0 8px 0;">Email Configuration Works!</h2>
				<p style="color: #64748b; margin: 0;">
					Your Resend API key and email address are configured correctly.
				</p>
			</div>

			<div style="margin-top: 24px; padding: 20px; background: #f8fafc; border-radius: 12px;">
				<h3 style="margin: 0 0 12px 0; color: #334155; font-size: 14px;">Configuration:</h3>
				<ul style="margin: 0; padding: 0 0 0 20px; color: #64748b; font-size: 14px;">
					<li>RESEND_API_KEY: ${RESEND_API_KEY?.substring(0, 10)}...</li>
					<li>NOTIFICATION_EMAIL: ${NOTIFICATION_EMAIL}</li>
					<li>PROJECT_NAME: ${PROJECT_NAME}</li>
				</ul>
			</div>
		</div>

		<div style="background: #f8fafc; padding: 20px 32px; text-align: center; border-top: 1px solid #e2e8f0;">
			<p style="margin: 0; font-size: 12px; color: #94a3b8;">
				Test email from ${PROJECT_NAME} A/B Testing Module
			</p>
		</div>
	</div>
</body>
</html>
	`;

	try {
		const { data, error } = await resend.emails.send({
			from: `${PROJECT_NAME} <onboarding@resend.dev>`,
			to: NOTIFICATION_EMAIL,
			subject: `✅ Test Email - ${PROJECT_NAME}`,
			html
		});

		if (error) {
			console.error('\n   ❌ Error:', error);
			process.exit(1);
		}

		console.log('\n   ✅ Email sent successfully!');
		console.log(`   Message ID: ${data?.id}`);
		console.log('\n   Check your inbox for the test email.\n');
	} catch (error) {
		console.error('\n   ❌ Error:', error);
		process.exit(1);
	}
}

main();
