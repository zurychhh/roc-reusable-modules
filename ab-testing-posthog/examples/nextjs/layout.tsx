'use client';

/**
 * Next.js Root Layout - PostHog Initialization
 *
 * Initialize PostHog once in the root layout.
 * Make sure this is a Client Component ('use client').
 */

import { useEffect } from 'react';
import { initPostHog } from '@/lib/posthog';

export default function RootLayout({
	children
}: {
	children: React.ReactNode;
}) {
	useEffect(() => {
		initPostHog();
	}, []);

	return (
		<html lang="en">
			<body>{children}</body>
		</html>
	);
}
