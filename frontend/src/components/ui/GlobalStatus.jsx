import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, ChevronRight, Activity, BrainCircuit } from 'lucide-react';
import clsx from 'clsx';
import './GlobalStatus.css';

/**
 * Global Inline Status Bar
 * Displays current backend activity (e.g., "Formulating Answer...") below the OmniHeader.
 * Expandable to show more details if needed.
 */
export default function GlobalStatus({ activity, isProcessing, logs }) {
    const [expanded, setExpanded] = useState(false);
    const logContainerRef = useRef(null);

    // Auto-scroll logs
    useEffect(() => {
        if (expanded && logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [logs, expanded]);

    if (!isProcessing && !activity) return null;

    return (
        <div className="global-status-bar">
            <div
                className="status-header"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-2">
                    <ChevronRight size={14} className={clsx("text-muted transition-transform", { "rotate-90": expanded })} />
                    <span className="status-text font-mono text-xs text-muted">
                        {isProcessing ? "Processing..." : (activity === "Ready" ? "Task Backend" : activity)}
                    </span>
                </div>

                {/* Optional expand icon if we have more details later */}
                {/* <div className="expand-icon text-muted">
                    {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </div> */}
            </div>

            {/* Expandable content for logs/details */}
            {expanded && (
                <div
                    ref={logContainerRef}
                    className="status-details scroll-thin"
                    style={{ maxHeight: '200px', overflowY: 'auto' }}
                >
                    {logs && logs.length > 0 ? (
                        logs.map((log, idx) => (
                            <div key={idx} className="log-entry text-dim font-mono text-xs mb-1">
                                {log}
                            </div>
                        ))
                    ) : (
                        <div className="log-entry text-dim">No recent backend activity.</div>
                    )}
                </div>
            )}
        </div>
    );
}
