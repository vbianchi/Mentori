import { Activity, Square, Copy, CheckCircle2, FileText, Code, ClipboardCheck, Brain, EyeOff, Download } from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';
import Button from '../primitives/Button';
import IconButton from '../primitives/IconButton';
import Badge from '../primitives/Badge';
import './OmniHeader.css';

/**
 * Omni-Presence Header
 * Shows current activity, token usage, and global controls.
 *
 * New Layout (Phase 3.2):
 * - Left: Activity indicator + Task name badge
 * - Center: Global controls (Markdown, Copy, Stop, Thinking Toggle)
 * - Right: Connection status badges + Token counter
 */
export default function OmniHeader({
    currentActivity = "Ready",
    isProcessing = false,
    onStopTask,
    onCopyChat,
    onExportChat,
    tokenStats = { total: 0, input: 0, output: 0 },
    showMarkdown = true,
    onToggleMarkdown,
    activeTaskName = null,
    activeTaskDisplayId = null,
    connectionStatus = { backend: 'connected', tools: 'connected' },
    // Thinking toggle props
    thinkingOpen = true,
    onToggleThinking
}) {
    const [copiedChat, setCopiedChat] = useState(false);

    const handleCopyChat = () => {
        onCopyChat();
        setCopiedChat(true);
        setTimeout(() => setCopiedChat(false), 2000);
    };

    return (
        <div className="omni-header glass-panel">
            {/* Left: Stop + Task ID */}
            <div className="header-section left">
                {/* Stop Button */}
                <Button
                    variant="danger"
                    size="sm"
                    icon={<Square size={14} fill="currentColor" />}
                    onClick={onStopTask}
                    disabled={!isProcessing}
                    className={clsx("stop-btn-compact", { "hidden": !isProcessing })}
                    title="Stop Task"
                >
                    Stop
                </Button>

                {/* Task ID Badge */}
                {activeTaskDisplayId ? (
                    <span className="task-id-badge">task_{activeTaskDisplayId}</span>
                ) : (
                    <span className="activity-text">{currentActivity}</span>
                )}
            </div>

            {/* Center: View Controls */}
            <div className="header-section center">
                <IconButton
                    variant={showMarkdown ? "surface" : "ghost"}
                    icon={showMarkdown ? <FileText size={14} /> : <Code size={14} />}
                    title={showMarkdown ? "Disable Markdown" : "Enable Markdown"}
                    onClick={onToggleMarkdown}
                />

                {onToggleThinking && (
                    <IconButton
                        variant={thinkingOpen ? "surface" : "ghost"}
                        icon={thinkingOpen ? <Brain size={14} /> : <EyeOff size={14} />}
                        title={thinkingOpen ? "Collapse All Thinking" : "Expand All Thinking"}
                        onClick={onToggleThinking}
                    />
                )}

                <IconButton
                    variant="ghost"
                    icon={copiedChat ? <ClipboardCheck size={16} className="text-green-500" /> : <Copy size={14} />}
                    title={copiedChat ? "Copied!" : "Copy Full Conversation"}
                    onClick={handleCopyChat}
                />

                {onExportChat && (
                    <IconButton
                        variant="ghost"
                        icon={<Download size={14} />}
                        title="Export as Markdown (Ctrl+Shift+E)"
                        onClick={onExportChat}
                    />
                )}
            </div>

            {/* Right: Token Badge */}
            <div className="header-section right">
                <div className="token-badge-container">
                    <span className="token-label">Tokens</span>
                    <span className="token-total">{tokenStats.total.toLocaleString()}</span>
                    <span className="token-details">
                        <span className="token-in">↓{tokenStats.input.toLocaleString()}</span>
                        <span className="token-out">↑{tokenStats.output.toLocaleString()}</span>
                    </span>
                </div>
            </div>
        </div>
    );
}
