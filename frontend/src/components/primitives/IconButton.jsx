import React from 'react';
import clsx from 'clsx';
import './IconButton.css';

/**
 * IconButton - Icon-only button primitive
 *
 * Optimized for icon-only actions (copy, close, edit, delete, etc.)
 * Always square, consistent sizing across the app.
 *
 * Variants:
 * - ghost: Transparent, hover shows background (default)
 * - surface: Light background
 * - primary: Accent color background
 * - danger: Red background for destructive actions
 *
 * Sizes: sm, md, lg
 *
 * Features:
 * - Square aspect ratio
 * - Tooltip support via title attribute
 * - Full accessibility
 * - Consistent styling (fixes copy button issues)
 *
 * Usage:
 * <IconButton
 *   variant="ghost"
 *   size="md"
 *   icon={<Copy size={16} />}
 *   title="Copy content"
 *   onClick={handleCopy}
 * />
 */
export default function IconButton({
    icon,
    variant = 'ghost',
    size = 'md',
    disabled = false,
    onClick,
    className,
    title,
    type = 'button',
    ...props
}) {
    return (
        <button
            type={type}
            className={clsx(
                'icon-btn',
                `icon-btn-${variant}`,
                `icon-btn-${size}`,
                className
            )}
            onClick={onClick}
            disabled={disabled}
            title={title}
            aria-label={title}
            {...props}
        >
            <span className="icon-btn-content">
                {icon}
            </span>
        </button>
    );
}
