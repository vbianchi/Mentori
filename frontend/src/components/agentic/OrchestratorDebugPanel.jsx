import { useState, useEffect, useRef } from 'react';
import { Bug, X, ChevronDown, ChevronRight, Trash2, Download } from 'lucide-react';

/**
 * Debug panel for visualizing orchestrator event flow.
 * Toggle with Ctrl+Shift+D (or Cmd+Shift+D on Mac)
 */
export default function OrchestratorDebugPanel({
    isVisible,
    onClose,
    // Orchestrator state
    orchestratorPhase,
    isOrchestrated,
    stepStatuses,
    // Feed state
    feed,
    // Event log (array of {timestamp, type, data})
    eventLog,
    onClearLog
}) {
    const [activeTab, setActiveTab] = useState('events'); // 'events' | 'state' | 'feed'
    const [expandedEvents, setExpandedEvents] = useState(new Set());
    const [filterType, setFilterType] = useState('all');
    const logEndRef = useRef(null);

    // Auto-scroll to latest event
    useEffect(() => {
        if (activeTab === 'events' && logEndRef.current) {
            logEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [eventLog, activeTab]);

    if (!isVisible) return null;

    const toggleEventExpand = (index) => {
        const newExpanded = new Set(expandedEvents);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedEvents(newExpanded);
    };

    // Get unique event types for filter
    const eventTypes = ['all', ...new Set(eventLog.map(e => e.type))];

    // Filter events
    const filteredEvents = filterType === 'all'
        ? eventLog
        : eventLog.filter(e => e.type === filterType);

    // Color coding for event types
    const getEventColor = (type) => {
        const colors = {
            'session_info': 'text-blue-400',
            'orchestrator_thinking_start': 'text-purple-400',
            'orchestrator_thinking': 'text-purple-300',
            'plan_generated': 'text-green-400',
            'direct_answer_mode': 'text-yellow-400',
            'step_start': 'text-cyan-400',
            'step_complete': 'text-green-500',
            'step_failed': 'text-red-500',
            'tool_call': 'text-orange-400',
            'tool_result': 'text-orange-300',
            'chunk': 'text-gray-400',
            'thinking_chunk': 'text-gray-500',
            'status': 'text-gray-400',
            'token_usage': 'text-gray-500',
            'error': 'text-red-400',
            'complete': 'text-green-400',
        };
        return colors[type] || 'text-gray-400';
    };

    // Export log as JSON
    const handleExport = () => {
        const data = {
            exportedAt: new Date().toISOString(),
            orchestratorState: {
                phase: orchestratorPhase,
                isOrchestrated,
                stepStatuses
            },
            feed: feed,
            events: eventLog
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `orchestrator-debug-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="fixed bottom-0 right-0 w-[600px] h-[400px] bg-slate-900 border border-slate-700 rounded-tl-lg shadow-2xl z-50 flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-2 bg-slate-800 border-b border-slate-700 rounded-tl-lg">
                <div className="flex items-center gap-2">
                    <Bug className="w-4 h-4 text-purple-400" />
                    <span className="text-sm font-semibold text-white">Orchestrator Debug</span>
                    {isOrchestrated && (
                        <span className="px-2 py-0.5 text-xs bg-purple-600 text-white rounded">
                            {orchestratorPhase || 'init'}
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleExport}
                        className="p-1 text-gray-400 hover:text-white transition-colors"
                        title="Export debug log"
                    >
                        <Download className="w-4 h-4" />
                    </button>
                    <button
                        onClick={onClearLog}
                        className="p-1 text-gray-400 hover:text-white transition-colors"
                        title="Clear log"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                    <button
                        onClick={onClose}
                        className="p-1 text-gray-400 hover:text-white transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-700">
                {['events', 'state', 'feed'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 text-sm capitalize transition-colors ${
                            activeTab === tab
                                ? 'text-purple-400 border-b-2 border-purple-400 bg-slate-800/50'
                                : 'text-gray-400 hover:text-white'
                        }`}
                    >
                        {tab}
                        {tab === 'events' && (
                            <span className="ml-1 text-xs text-gray-500">({eventLog.length})</span>
                        )}
                        {tab === 'feed' && (
                            <span className="ml-1 text-xs text-gray-500">({feed.length})</span>
                        )}
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-2 font-mono text-xs">
                {/* Events Tab */}
                {activeTab === 'events' && (
                    <div className="space-y-1">
                        {/* Filter */}
                        <div className="sticky top-0 bg-slate-900 pb-2 z-10">
                            <select
                                value={filterType}
                                onChange={(e) => setFilterType(e.target.value)}
                                className="bg-slate-800 text-gray-300 text-xs px-2 py-1 rounded border border-slate-600"
                            >
                                {eventTypes.map(type => (
                                    <option key={type} value={type}>
                                        {type === 'all' ? 'All Events' : type}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {filteredEvents.map((event, idx) => (
                            <div
                                key={idx}
                                className="bg-slate-800/50 rounded p-1.5 hover:bg-slate-800 transition-colors"
                            >
                                <div
                                    className="flex items-center gap-2 cursor-pointer"
                                    onClick={() => toggleEventExpand(idx)}
                                >
                                    {expandedEvents.has(idx) ? (
                                        <ChevronDown className="w-3 h-3 text-gray-500" />
                                    ) : (
                                        <ChevronRight className="w-3 h-3 text-gray-500" />
                                    )}
                                    <span className="text-gray-500">{event.timestamp}</span>
                                    <span className={`font-semibold ${getEventColor(event.type)}`}>
                                        {event.type}
                                    </span>
                                    {event.data?.phase && (
                                        <span className="text-gray-500">phase={event.data.phase}</span>
                                    )}
                                    {event.data?.step_id && (
                                        <span className="text-cyan-500">{event.data.step_id}</span>
                                    )}
                                </div>
                                {expandedEvents.has(idx) && (
                                    <pre className="mt-1 ml-5 text-gray-400 whitespace-pre-wrap break-all max-h-32 overflow-auto">
                                        {JSON.stringify(event.data, null, 2)}
                                    </pre>
                                )}
                            </div>
                        ))}
                        <div ref={logEndRef} />
                    </div>
                )}

                {/* State Tab */}
                {activeTab === 'state' && (
                    <div className="space-y-4">
                        <div>
                            <h3 className="text-purple-400 font-semibold mb-2">Orchestrator State</h3>
                            <div className="bg-slate-800 rounded p-2 space-y-1">
                                <div className="flex justify-between">
                                    <span className="text-gray-400">isOrchestrated:</span>
                                    <span className={isOrchestrated ? 'text-green-400' : 'text-gray-500'}>
                                        {String(isOrchestrated)}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">phase:</span>
                                    <span className="text-purple-400">{orchestratorPhase || 'null'}</span>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h3 className="text-cyan-400 font-semibold mb-2">Step Statuses</h3>
                            <div className="bg-slate-800 rounded p-2">
                                {Object.keys(stepStatuses).length === 0 ? (
                                    <span className="text-gray-500">No steps tracked</span>
                                ) : (
                                    <div className="space-y-1">
                                        {Object.entries(stepStatuses).map(([stepId, status]) => (
                                            <div key={stepId} className="flex justify-between">
                                                <span className="text-gray-400">{stepId}:</span>
                                                <span className={
                                                    status === 'completed' ? 'text-green-400' :
                                                    status === 'running' ? 'text-blue-400' :
                                                    status === 'failed' ? 'text-red-400' :
                                                    'text-gray-500'
                                                }>
                                                    {status}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Feed Tab */}
                {activeTab === 'feed' && (
                    <div className="space-y-1">
                        {feed.length === 0 ? (
                            <span className="text-gray-500">Feed is empty</span>
                        ) : (
                            feed.map((item, idx) => (
                                <div
                                    key={idx}
                                    className="bg-slate-800/50 rounded p-1.5 hover:bg-slate-800 transition-colors cursor-pointer"
                                    onClick={() => toggleEventExpand(`feed-${idx}`)}
                                >
                                    <div className="flex items-center gap-2">
                                        {expandedEvents.has(`feed-${idx}`) ? (
                                            <ChevronDown className="w-3 h-3 text-gray-500" />
                                        ) : (
                                            <ChevronRight className="w-3 h-3 text-gray-500" />
                                        )}
                                        <span className="text-gray-500">[{idx}]</span>
                                        <span className={`font-semibold ${
                                            item.type === 'user' ? 'text-cyan-400' :
                                            item.type === 'assistant' ? 'text-green-400' :
                                            item.type === 'tool' ? 'text-orange-400' :
                                            item.type === 'plan' ? 'text-purple-400' :
                                            item.type === 'step_progress' ? 'text-blue-400' :
                                            'text-gray-400'
                                        }`}>
                                            {item.type}
                                        </span>
                                        {item.toolName && (
                                            <span className="text-orange-300">{item.toolName}</span>
                                        )}
                                        {item.stepId && (
                                            <span className="text-cyan-500">{item.stepId}</span>
                                        )}
                                        {item.status && (
                                            <span className={
                                                item.status === 'completed' || item.status === 'success' ? 'text-green-400' :
                                                item.status === 'running' ? 'text-blue-400' :
                                                item.status === 'failed' ? 'text-red-400' :
                                                'text-gray-500'
                                            }>
                                                [{item.status}]
                                            </span>
                                        )}
                                    </div>
                                    {expandedEvents.has(`feed-${idx}`) && (
                                        <pre className="mt-1 ml-5 text-gray-400 whitespace-pre-wrap break-all max-h-32 overflow-auto">
                                            {JSON.stringify(item, null, 2)}
                                        </pre>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-3 py-1.5 bg-slate-800 border-t border-slate-700 text-xs text-gray-500">
                Press <kbd className="px-1 py-0.5 bg-slate-700 rounded">Ctrl+Shift+D</kbd> to toggle
            </div>
        </div>
    );
}
