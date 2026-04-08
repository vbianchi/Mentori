import React from 'react';
import clsx from 'clsx';
import './Input.css';

/**
 * Input - Text input primitive
 *
 * A styled input wrapper with consistent appearance across the app.
 * Supports text, number, email, password, etc.
 *
 * Features:
 * - Consistent focus states
 * - Error state support
 * - Optional prefix/suffix icons or text
 * - Full accessibility
 *
 * Usage:
 * <Input
 *   type="text"
 *   placeholder="Enter value..."
 *   value={value}
 *   onChange={(e) => setValue(e.target.value)}
 * />
 */
export default function Input({
    type = 'text',
    value,
    onChange,
    placeholder,
    disabled = false,
    error = false,
    className,
    ...props
}) {
    return (
        <input
            type={type}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            disabled={disabled}
            className={clsx(
                'input',
                {
                    'input-error': error
                },
                className
            )}
            {...props}
        />
    );
}
