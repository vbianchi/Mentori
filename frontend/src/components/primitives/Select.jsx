import React from 'react';
import clsx from 'clsx';
import './Select.css';

/**
 * Select - Dropdown select primitive
 *
 * A styled select wrapper with consistent appearance.
 * Matches the cosmic night theme.
 *
 * Features:
 * - Consistent focus states
 * - Custom arrow icon
 * - Full accessibility
 *
 * Usage:
 * <Select value={value} onChange={(e) => setValue(e.target.value)}>
 *   <option value="option1">Option 1</option>
 *   <option value="option2">Option 2</option>
 * </Select>
 */
export default function Select({
    children,
    value,
    onChange,
    disabled = false,
    className,
    ...props
}) {
    return (
        <div className="select-wrapper">
            <select
                value={value}
                onChange={onChange}
                disabled={disabled}
                className={clsx('select', className)}
                {...props}
            >
                {children}
            </select>
            <svg
                className="select-arrow"
                width="12"
                height="12"
                viewBox="0 0 12 12"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
            >
                <path
                    d="M3 4.5L6 7.5L9 4.5"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            </svg>
        </div>
    );
}
