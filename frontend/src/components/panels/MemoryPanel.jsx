import { useState, useEffect } from 'react';
import { BookOpen, Trash2, RefreshCw, Clock, FileText, HelpCircle } from 'lucide-react';
import clsx from 'clsx';
import config from '../../config';
import './MemoryPanel.css';

/**
 * Memory Panel - Shows task session memory vault status
 * Part of Phase 2B: Task Session Memory
 */
export default function MemoryPanel({ taskId, onRefresh }) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [memoryStats, setMemoryStats] = useState(null);
    const [deletingSession, setDeletingSession] = useState(null);

    useEffect(() => {
        if (taskId) {
            fetchMemoryStats();
        }
    }, [taskId]);

    const fetchMemoryStats = async () => {
        if (!taskId) return;

        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/tasks/${taskId}/memory`, {
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (!res.ok) {
                throw new Error("Failed to load memory stats");
            }

            const data = await res.json();
            setMemoryStats(data);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteSession = async (sessionId) => {
        if (!taskId || !sessionId) return;

        setDeletingSession(sessionId);

        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/tasks/${taskId}/memory/sessions/${sessionId}`, {
                method: 'DELETE',
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (!res.ok) {
                throw new Error("Failed to delete session");
            }

            // Refresh stats
            await fetchMemoryStats();
            if (onRefresh) onRefresh();
        } catch (e) {
            setError(e.message);
        } finally {
            setDeletingSession(null);
        }
    };

    const formatTimestamp = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getUsageColor = (percent) => {
        if (percent >= 90) return 'usage-critical';
        if (percent >= 70) return 'usage-warning';
        return 'usage-normal';
    };

    if (!taskId) {
        return (
            <div className="memory-panel">
                <div className="memory-empty">
                    <BookOpen size={24} className="text-muted" />
                    <p>Select a task to view memory</p>
                </div>
            </div>
        );
    }

    return (
        <div className="memory-panel">
            {/* Header */}
            <div className="memory-header">
                <div className="memory-title">
                    <BookOpen size={16} className="text-accent-secondary" />
                    <span>Task Memory</span>
                </div>
                <button
                    className="memory-refresh-btn"
                    onClick={fetchMemoryStats}
                    disabled={loading}
                    title="Refresh"
                >
                    <RefreshCw size={14} className={clsx({ 'animate-spin': loading })} />
                </button>
            </div>

            {/* Error State */}
            {error && (
                <div className="memory-error">
                    <span>{error}</span>
                </div>
            )}

            {/* Loading State */}
            {loading && !memoryStats && (
                <div className="memory-loading">
                    <RefreshCw size={20} className="animate-spin text-muted" />
                    <span>Loading memory...</span>
                </div>
            )}

            {/* Content */}
            {memoryStats && (
                <>
                    {/* Memory Injection Budget */}
                    <div className="memory-budget">
                        <div className="budget-header">
                            <span className="budget-label">Memory Injection Budget</span>
                            <span className="budget-value">
                                {memoryStats.total_tokens.toLocaleString()} / {memoryStats.max_tokens.toLocaleString()} tokens
                            </span>
                        </div>
                        <div className="budget-bar">
                            <div
                                className={clsx('budget-fill', getUsageColor(memoryStats.usage_percent))}
                                style={{ width: `${Math.min(memoryStats.usage_percent, 100)}%` }}
                            />
                        </div>
                        <div className="budget-percent">
                            {memoryStats.usage_percent}% used
                            <span
                                className="budget-hint"
                                title="Past-session memory injected into each new prompt. Separate from the full model context window and the distillation threshold."
                            >
                                {' '}— past-session context injected per prompt
                            </span>
                        </div>
                    </div>

                    {/* Session List */}
                    <div className="memory-sessions">
                        <div className="sessions-header">
                            <span>Sessions ({memoryStats.session_count})</span>
                            <HelpCircle
                                size={12}
                                className="text-muted cursor-help"
                                title="Each session represents one query/response cycle. Delete old sessions to free up context budget."
                            />
                        </div>

                        {memoryStats.sessions.length === 0 ? (
                            <div className="sessions-empty">
                                <FileText size={18} className="text-muted" />
                                <p>No sessions recorded yet</p>
                                <span className="text-xs text-muted">Sessions are created after each query</span>
                            </div>
                        ) : (
                            <div className="sessions-list">
                                {memoryStats.sessions.map((session) => (
                                    <div key={session.id} className="session-card">
                                        <div className="session-main">
                                            <div className="session-intent" title={session.intent}>
                                                {session.intent}
                                            </div>
                                            <div className="session-meta">
                                                <span className="session-time">
                                                    <Clock size={10} />
                                                    {formatTimestamp(session.timestamp)}
                                                </span>
                                                <span className="session-tokens">
                                                    {session.tokens.toLocaleString()} tokens
                                                </span>
                                                {session.artifacts > 0 && (
                                                    <span className="session-artifacts">
                                                        <FileText size={10} />
                                                        {session.artifacts}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <button
                                            className="session-delete-btn"
                                            onClick={() => handleDeleteSession(session.id)}
                                            disabled={deletingSession === session.id}
                                            title="Delete session"
                                        >
                                            {deletingSession === session.id ? (
                                                <RefreshCw size={12} className="animate-spin" />
                                            ) : (
                                                <Trash2 size={12} />
                                            )}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
