import React from 'react';
import { CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-react';
import './Toast.css';

const iconMap = {
    success: CheckCircle,
    error: XCircle,
    info: Info,
    warning: AlertTriangle
};

export default function Toast({ toasts, onRemove }) {
    if (toasts.length === 0) return null;

    return (
        <div className="toast-container">
            {toasts.map(toast => {
                const Icon = iconMap[toast.type] || Info;

                return (
                    <div key={toast.id} className={`toast toast-${toast.type}`}>
                        <Icon size={16} className="toast-icon" />
                        <span className="toast-message">{toast.message}</span>
                        <button
                            className="toast-close"
                            onClick={() => onRemove(toast.id)}
                            aria-label="Close notification"
                        >
                            <X size={14} />
                        </button>
                    </div>
                );
            })}
        </div>
    );
}
