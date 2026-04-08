import React from 'react';
import { ChevronRight, Home } from 'lucide-react';

/**
 * Breadcrumb navigation for file explorer
 * Shows the current path and allows quick navigation
 */
export default function Breadcrumb({ currentPath, onNavigate }) {
    // Parse path into parts
    const parts = currentPath && currentPath !== '.' ? currentPath.split('/').filter(Boolean) : [];

    return (
        <div className="file-breadcrumb">
            <button
                className={`breadcrumb-item ${parts.length === 0 ? 'active' : ''}`}
                onClick={() => onNavigate('')}
                title="Root workspace"
            >
                <Home size={12} />
                <span>Workspace</span>
            </button>

            {parts.map((part, idx) => {
                const path = parts.slice(0, idx + 1).join('/');
                const isLast = idx === parts.length - 1;

                return (
                    <React.Fragment key={path}>
                        <ChevronRight size={12} className="breadcrumb-separator" />
                        <button
                            className={`breadcrumb-item ${isLast ? 'active' : ''}`}
                            onClick={() => !isLast && onNavigate(path)}
                            disabled={isLast}
                            title={part}
                        >
                            {part}
                        </button>
                    </React.Fragment>
                );
            })}
        </div>
    );
}
