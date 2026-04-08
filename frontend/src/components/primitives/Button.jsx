import React from 'react';
import clsx from 'clsx';
import './Button.css';

/**
 * Button - Primary action component
 *
 * Variants:
 * - primary: Main call-to-action (purple accent)
 * - secondary: Secondary actions (cyan accent)
 * - ghost: Minimal styling, transparent background
 * - danger: Destructive actions (red)
 *
 * Sizes: sm, md, lg
 *
 * Features:
 * - Icon support (prefix or standalone)
 * - Loading state with spinner
 * - Disabled state
 * - Full accessibility (aria attributes)
 *
 * Usage:
 * <Button variant="primary" size="md" icon={<SendHorizontal />}>
 *   Send
 * </Button>
 */
export default function Button({
    children,
    variant = 'primary',
    size = 'md',
    icon = null,
    loading = false,
    disabled = false,
    onClick,
    className,
    type = 'button',
    ...props
}) {
    const hasText = React.Children.count(children) > 0;

    return (
        <button
            type={type}
            className={clsx(
                'btn',
                `btn-${variant}`,
                `btn-${size}`,
                {
                    'btn-loading': loading,
                    'btn-icon-only': icon && !hasText
                },
                className
            )}
            onClick={onClick}
            disabled={disabled || loading}
            aria-busy={loading}
            {...props}
        >
            {loading ? (
                <>
                    <span className="btn-spinner" aria-hidden="true">
                        <svg className="spinner-circle" viewBox="0 0 24 24">
                            <circle
                                className="spinner-track"
                                cx="12"
                                cy="12"
                                r="10"
                                fill="none"
                                strokeWidth="3"
                            />
                            <circle
                                className="spinner-path"
                                cx="12"
                                cy="12"
                                r="10"
                                fill="none"
                                strokeWidth="3"
                                strokeDasharray="60"
                                strokeDashoffset="20"
                            />
                        </svg>
                    </span>
                    <span className="btn-content" style={{ opacity: 0.6 }}>
                        {icon && <span className="btn-icon">{icon}</span>}
                        {children}
                    </span>
                </>
            ) : (
                <>
                    {icon && <span className="btn-icon">{icon}</span>}
                    {children}
                </>
            )}
        </button>
    );
}
