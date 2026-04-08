import React, { useEffect, useRef } from 'react';
import clsx from 'clsx';

export default function ContextMenu({ x, y, actions, onClose }) {
    const menuRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (menuRef.current && !menuRef.current.contains(e.target)) {
                onClose();
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [onClose]);

    // Adjust position if it flows offscreen (basic)
    const style = {
        top: y,
        left: x,
    };

    return (
        <div
            ref={menuRef}
            className="fixed z-50 min-w-[160px] bg-gray-900 border border-white/10 rounded-lg shadow-xl py-1 animate-in fade-in zoom-in-95 duration-100"
            style={style}
        >
            {actions.map((action, idx) => (
                <button
                    key={idx}
                    className={clsx(
                        "w-full text-left px-3 py-1.5 text-sm flex items-center gap-2 hover:bg-white/10 transition-colors",
                        action.danger ? "text-red-400 hover:text-red-300" : "text-gray-200"
                    )}
                    onClick={() => {
                        action.onClick();
                        onClose();
                    }}
                >
                    {action.icon && <span className="opacity-70">{action.icon}</span>}
                    {action.label}
                </button>
            ))}
        </div>
    );
}
