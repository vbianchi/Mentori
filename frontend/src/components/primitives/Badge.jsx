import React from 'react';
import clsx from 'clsx';
import './Badge.css';

/**
 * Badge - Label and status indicator primitive
 *
 * Used for:
 * - Status indicators (connected, disconnected, processing)
 * - Labels and tags (task names, categories)
 * - Counters and counts
 *
 * Variants:
 * - default: Neutral gray
 * - primary: Purple accent (active states, task names)
 * - success: Green (connected, completed)
 * - warning: Amber (warnings, attention needed)
 * - error: Red (errors, disconnected)
 *
 * Sizes: sm, md
 *
 * Special Features:
 * - dot: Shows a colored dot indicator (for connection status)
 * - pill: Fully rounded edges
 *
 * Usage:
 * <Badge variant="success">Connected</Badge>
 * <Badge variant="error" dot>Disconnected</Badge>
 * <Badge variant="primary" size="sm">Task Name</Badge>
 */
export default function Badge({
    children,
    variant = 'default',
    size = 'md',
    dot = false,
    pill = false,
    className,
    ...props
}) {
    return (
        <span
            className={clsx(
                'badge',
                `badge-${variant}`,
                `badge-${size}`,
                {
                    'badge-dot': dot,
                    'badge-pill': pill
                },
                className
            )}
            {...props}
        >
            {dot && <span className="badge-dot-indicator" aria-hidden="true" />}
            {children}
        </span>
    );
}
