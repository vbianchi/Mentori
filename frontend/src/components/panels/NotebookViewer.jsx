import React, { useState, useEffect, useRef, memo, Component } from 'react';
import { Play, Check, X, Clock, Code, FileText, ChevronDown, ChevronRight, AlertCircle, RefreshCw, PlayCircle, Plus, Trash2, ChevronLeft, Square, RotateCcw } from 'lucide-react';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeHighlight from 'rehype-highlight';
import rehypeKatex from 'rehype-katex';
import 'highlight.js/styles/atom-one-dark.css';
import './NotebookViewer.css';

/**
 * Error Boundary to catch rendering errors
 */
class NotebookErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('[NotebookViewer Error]', error);
        console.error('[NotebookViewer Error Stack]', errorInfo?.componentStack);
        this.setState({ errorInfo });
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="notebook-viewer" style={{ padding: '1rem', color: '#ef4444' }}>
                    <h3 style={{ margin: '0 0 0.5rem 0' }}>NotebookViewer Error</h3>
                    <pre style={{
                        background: 'rgba(239, 68, 68, 0.1)',
                        padding: '0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        overflow: 'auto'
                    }}>
                        {this.state.error?.toString()}
                        {this.state.errorInfo?.componentStack}
                    </pre>
                </div>
            );
        }
        return this.props.children;
    }
}

/**
 * Status indicator for cell execution state
 */
const CellStatus = ({ status }) => {
    const statusConfig = {
        idle: { icon: <Clock size={12} />, color: 'text-muted', label: 'Idle' },
        queued: { icon: <Clock size={12} />, color: 'text-blue-400', label: 'Queued' },
        running: { icon: <Play size={12} className="animate-pulse" />, color: 'text-yellow-400', label: 'Running' },
        success: { icon: <Check size={12} />, color: 'text-green-400', label: 'Success' },
        error: { icon: <X size={12} />, color: 'text-red-400', label: 'Error' }
    };

    const config = statusConfig[status] || statusConfig.idle;

    return (
        <span className={clsx('cell-status', config.color)} title={config.label}>
            {config.icon}
        </span>
    );
};

/**
 * Code block with syntax highlighting
 */
const CodeBlock = ({ source, language = 'python' }) => {
    return (
        <pre className="cell-code-block">
            <code className={`language-${language}`}>
                {source}
            </code>
        </pre>
    );
};

/**
 * Cell output renderer - handles different output types (memoized)
 */
const CellOutput = memo(({ output }) => {
    // Defensive check for undefined/null output
    if (!output || typeof output !== 'object') {
        return null;
    }

    const { output_type, data, text, name, ename, evalue, traceback } = output;

    // Stream output (stdout/stderr)
    if (output_type === 'stream') {
        const isError = name === 'stderr';
        return (
            <div className={clsx('cell-output-stream', { 'stderr': isError })}>
                <pre>{text}</pre>
            </div>
        );
    }

    // Error output
    if (output_type === 'error') {
        return (
            <div className="cell-output-error">
                <div className="error-header">
                    <AlertCircle size={14} />
                    <span className="error-name">{ename}</span>: <span className="error-value">{evalue}</span>
                </div>
                {traceback && traceback.length > 0 && (
                    <pre className="error-traceback">
                        {traceback.map((line, i) => (
                            <div key={i} dangerouslySetInnerHTML={{ __html: ansiToHtml(line) }} />
                        ))}
                    </pre>
                )}
            </div>
        );
    }

    // Execute result or display_data
    if (output_type === 'execute_result' || output_type === 'display_data') {
        // Check for image data
        if (data?.['image/png']) {
            return (
                <div className="cell-output-image">
                    <img src={`data:image/png;base64,${data['image/png']}`} alt="Output" />
                </div>
            );
        }
        if (data?.['image/jpeg']) {
            return (
                <div className="cell-output-image">
                    <img src={`data:image/jpeg;base64,${data['image/jpeg']}`} alt="Output" />
                </div>
            );
        }
        if (data?.['image/svg+xml']) {
            return (
                <div className="cell-output-image" dangerouslySetInnerHTML={{ __html: data['image/svg+xml'] }} />
            );
        }

        // HTML output
        if (data?.['text/html']) {
            return (
                <div className="cell-output-html" dangerouslySetInnerHTML={{ __html: data['text/html'] }} />
            );
        }

        // Text output
        if (data?.['text/plain']) {
            return (
                <div className="cell-output-text">
                    <pre>{data['text/plain']}</pre>
                </div>
            );
        }
    }

    return null;
});

CellOutput.displayName = 'CellOutput';

/**
 * Simple ANSI to HTML converter for traceback coloring
 */
const ansiToHtml = (text) => {
    if (!text) return '';

    // Strip ANSI codes for now (simplified version)
    // A full implementation would convert colors, but this keeps it simple
    return text
        .replace(/\x1b\[[0-9;]*m/g, '')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
};

/**
 * Single notebook cell component (memoized to prevent re-renders)
 */
const NotebookCell = memo(({ cell, isActive, onExecute, onUpdate, onDelete, notebookName, autoEdit = false }) => {
    const [collapsed, setCollapsed] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [editSource, setEditSource] = useState('');
    const cellRef = useRef(null);
    const textareaRef = useRef(null);

    // Auto-enter edit mode when a cell is freshly created
    useEffect(() => {
        if (autoEdit) {
            setEditSource(cell?.source || '');
            setIsEditing(true);
            cellRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Auto-scroll to active cell
    useEffect(() => {
        if (isActive && cellRef.current) {
            cellRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }, [isActive]);

    // Focus textarea when entering edit mode
    useEffect(() => {
        if (isEditing && textareaRef.current) {
            textareaRef.current.focus();
            // Move cursor to end
            textareaRef.current.selectionStart = textareaRef.current.value.length;
        }
    }, [isEditing]);

    // Defensive check for undefined/null cell
    if (!cell || typeof cell !== 'object') {
        return null;
    }

    const { id, cell_type, source = '', outputs = [], status, execution_count } = cell;
    const isCode = cell_type === 'code';
    // Ensure outputs is an array and filter out null/undefined entries
    const safeOutputs = Array.isArray(outputs) ? outputs.filter(o => o != null) : [];
    const hasOutputs = safeOutputs.length > 0;
    const hasError = status === 'error' || safeOutputs.some(o => o.output_type === 'error');
    const isRunning = status === 'running';

    const handleStartEdit = () => {
        setEditSource(source);
        setIsEditing(true);
    };

    const handleCancelEdit = () => {
        setIsEditing(false);
        setEditSource('');
    };

    const handleSaveEdit = async () => {
        if (onUpdate && editSource !== source) {
            const success = await onUpdate(notebookName, id, editSource);
            if (success) {
                setIsEditing(false);
            }
        } else {
            setIsEditing(false);
        }
    };

    const handleKeyDown = (e) => {
        // Ctrl/Cmd + Enter to save
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleSaveEdit();
        }
        // Escape to cancel
        if (e.key === 'Escape') {
            handleCancelEdit();
        }
    };

    const handleRun = () => {
        if (onExecute && isCode && !isRunning) {
            onExecute(notebookName, id);
        }
    };

    return (
        <div
            ref={cellRef}
            className={clsx('notebook-cell', {
                'code-cell': isCode,
                'markdown-cell': !isCode,
                'is-active': isActive,
                'has-error': hasError,
                'is-running': isRunning,
                'is-editing': isEditing
            })}
        >
            {/* Cell header */}
            <div className="cell-header">
                <div className="cell-header-left">
                    <button
                        className="cell-collapse-btn"
                        onClick={() => setCollapsed(!collapsed)}
                    >
                        {collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                    </button>
                    <span className="cell-type-icon">
                        {isCode ? <Code size={14} /> : <FileText size={14} />}
                    </span>
                    <span className="cell-index">[{execution_count ?? ' '}]</span>
                </div>
                <div className="cell-header-right">
                    {/* Action buttons */}
                    {isCode && onExecute && (
                        <button
                            className={clsx('cell-action-btn run-btn', { 'is-running': isRunning })}
                            onClick={handleRun}
                            disabled={isRunning}
                            title={isRunning ? "Running..." : "Run cell (Shift+Enter)"}
                        >
                            {isRunning ? <Clock size={12} className="animate-spin" /> : <Play size={12} />}
                        </button>
                    )}
                    {onUpdate && !isEditing && (
                        <button
                            className="cell-action-btn edit-btn"
                            onClick={handleStartEdit}
                            title="Edit cell"
                        >
                            <FileText size={12} />
                        </button>
                    )}
                    {isEditing && (
                        <>
                            <button
                                className="cell-action-btn save-btn"
                                onClick={handleSaveEdit}
                                title="Save (Ctrl+Enter)"
                            >
                                <Check size={12} />
                            </button>
                            <button
                                className="cell-action-btn cancel-btn"
                                onClick={handleCancelEdit}
                                title="Cancel (Esc)"
                            >
                                <X size={12} />
                            </button>
                        </>
                    )}
                    {onDelete && (
                        <button
                            className="cell-action-btn delete-btn"
                            onClick={() => onDelete(notebookName, id)}
                            title="Delete cell"
                        >
                            <Trash2 size={12} />
                        </button>
                    )}
                    <CellStatus status={status} />
                    <span className="cell-id">{id?.slice(0, 8)}</span>
                </div>
            </div>

            {/* Cell content */}
            {!collapsed && (
                <div className="cell-content">
                    {isEditing ? (
                        <textarea
                            ref={textareaRef}
                            className="cell-edit-textarea"
                            value={editSource}
                            onChange={(e) => setEditSource(e.target.value)}
                            onKeyDown={handleKeyDown}
                            spellCheck={false}
                            placeholder="Enter code..."
                        />
                    ) : isCode ? (
                        <CodeBlock source={source} />
                    ) : (
                        <div className="markdown-content">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm, remarkMath]}
                                rehypePlugins={[rehypeHighlight, rehypeKatex]}
                            >
                                {source}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>
            )}

            {/* Cell outputs */}
            {!collapsed && hasOutputs && (
                <div className="cell-outputs">
                    {safeOutputs.map((output, i) => (
                        <CellOutput key={i} output={output} />
                    ))}
                </div>
            )}
        </div>
    );
});

// Display name for debugging
NotebookCell.displayName = 'NotebookCell';

/**
 * Hover divider shown between cells (and at top/bottom) for inserting new cells.
 * position = index to insert before (0 = top, cells.length = bottom/append).
 */
const InsertCellDivider = ({ notebookName, position, onAddCell }) => {
    const [hovered, setHovered] = useState(false);
    return (
        <div
            className={clsx('cell-insert-divider', { 'is-hovered': hovered })}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
        >
            <div className="cell-insert-line" />
            <div className="cell-insert-btns">
                <button
                    className="cell-insert-btn"
                    onClick={() => onAddCell(notebookName, 'code', position)}
                    title="Insert code cell here"
                >
                    <Plus size={11} /><Code size={11} /> Code
                </button>
                <button
                    className="cell-insert-btn"
                    onClick={() => onAddCell(notebookName, 'markdown', position)}
                    title="Insert markdown cell here"
                >
                    <Plus size={11} /><FileText size={11} /> Markdown
                </button>
            </div>
        </div>
    );
};

/**
 * Inner NotebookViewer component (wrapped by error boundary)
 */
// Kernel display metadata
const KERNEL_INFO = {
    python3: { label: 'Python 3.12', badge: 'PY',  color: '#4B8BBE' },
    ir:      { label: 'R 4.5.0',    badge: 'R',   color: '#276DC3' },
};

function NotebookViewerInner({
    notebookName = 'Untitled',
    cells = [],
    activeCellId = null,
    isLoading = false,
    isEmpty = false,
    notebooks = [],
    onSelectNotebook = null,
    onRefresh = null,
    onExecuteCell = null,
    onUpdateCell = null,
    onRunAll = null,
    isRunningAll = false,
    onCreateNotebook = null,
    onAddCell = null,
    onDeleteCell = null,
    onCloseNotebook = null,
    kernelName = 'python3',
    onStopKernel = null,
    onRestartKernel = null,
}) {
    const [newNbName, setNewNbName] = useState('');
    const [newNbKernel, setNewNbKernel] = useState('python3');
    const [creatingNb, setCreatingNb] = useState(false);
    const [newCellId, setNewCellId] = useState(null);
    const containerRef = useRef(null);

    // Wrapper that captures the returned cell_id so we can auto-edit it
    // position: 0-based index to insert before; null/undefined = append at end
    const handleAddCellWithAutoEdit = async (nbName, cellType, position) => {
        const cellId = await onAddCell?.(nbName, cellType, position);
        if (cellId) setNewCellId(cellId);
    };

    const handleCreateNotebook = async () => {
        const name = newNbName.trim() || 'notebook';
        setCreatingNb(true);
        try {
            await onCreateNotebook?.(name, newNbKernel);
            setNewNbName('');
        } finally {
            setCreatingNb(false);
        }
    };

    // Debug logging
    useEffect(() => {
        console.log('[NotebookViewer] Rendering:', { notebookName, cellCount: cells?.length, isEmpty, activeCellId });
    }, [notebookName, cells, isEmpty, activeCellId]);

    // Ensure cells is always an array and filter out null/undefined entries
    const safeCells = Array.isArray(cells) ? cells.filter(c => c != null) : [];

    // Auto-scroll to bottom when new cells are added
    useEffect(() => {
        if (containerRef.current && safeCells.length > 0) {
            const container = containerRef.current;
            // Only auto-scroll if user is near the bottom
            const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 200;
            if (isNearBottom) {
                container.scrollTop = container.scrollHeight;
            }
        }
    }, [safeCells.length]);

    if (isLoading) {
        return (
            <div className="notebook-viewer-loading">
                <div className="loading-spinner" />
                <span>Loading notebook...</span>
            </div>
        );
    }

    // Show empty state with notebook selector if no notebook is loaded
    if (isEmpty) {
        // notebooks is now an array of objects {name, kernel, kernel_display, cell_count, code_cells}
        // OR legacy array of strings — normalise both
        const nbItems = notebooks.map(nb =>
            typeof nb === 'string'
                ? { name: nb, kernel: 'python3', kernel_display: 'Python 3', cell_count: null, code_cells: null }
                : nb
        );

        // Map kernel spec names to display info.
        // kernel_display from IRkernel is just "R" — we enrich it here.
        const KERNEL_BADGE = {
            python3: { label: 'PY', color: '#4B8BBE', display: 'Python 3.12' },
            ir:      { label: 'R',  color: '#276DC3', display: 'R 4.5.0'    },
        };

        return (
            <div className="notebook-viewer">
                <div className="notebook-selector-panel">
                    {/* Header row */}
                    <div className="nb-selector-header">
                        <div className="nb-selector-title">
                            <Code size={16} />
                            <span>Notebooks</span>
                        </div>
                        {onRefresh && (
                            <button className="nb-selector-refresh" onClick={onRefresh} title="Refresh list">
                                <RefreshCw size={13} />
                            </button>
                        )}
                    </div>

                    {/* Notebook table */}
                    {nbItems.length > 0 ? (
                        <table className="nb-selector-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Kernel</th>
                                    <th className="text-right">Cells</th>
                                    <th className="text-right">Code</th>
                                </tr>
                            </thead>
                            <tbody>
                                {nbItems.map((nb) => {
                                    const ki = KERNEL_BADGE[nb.kernel] || KERNEL_BADGE.python3;
                                    return (
                                        <tr
                                            key={nb.name}
                                            className="nb-selector-row"
                                            onClick={() => onSelectNotebook?.(nb.name)}
                                            title={`Open ${nb.name}.ipynb`}
                                        >
                                            <td className="nb-name-col">
                                                <FileText size={12} className="nb-name-icon" />
                                                {nb.name}
                                            </td>
                                            <td>
                                                <span className="nb-kernel-chip" style={{ background: ki.color }}>
                                                    {ki.label}
                                                </span>
                                                <span className="nb-kernel-text">
                                                    {ki.display || nb.kernel_display}
                                                </span>
                                            </td>
                                            <td className="text-right nb-count-col">{nb.cell_count ?? '—'}</td>
                                            <td className="text-right nb-count-col">{nb.code_cells ?? '—'}</td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    ) : (
                        <div className="nb-selector-empty">
                            <Code size={32} className="text-muted" />
                            <p>No notebooks yet</p>
                        </div>
                    )}

                    {/* Create form */}
                    {onCreateNotebook && (
                        <div className="nb-create-row">
                            <input
                                type="text"
                                id="nb-name-input"
                                name="notebook-name"
                                className="notebook-name-input"
                                placeholder="new notebook name"
                                value={newNbName}
                                onChange={e => setNewNbName(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleCreateNotebook()}
                                disabled={creatingNb}
                            />
                            <select
                                className="notebook-kernel-select"
                                value={newNbKernel}
                                onChange={e => setNewNbKernel(e.target.value)}
                                disabled={creatingNb}
                                title="Select kernel"
                            >
                                <option value="python3">Python 3.12</option>
                                <option value="ir">R 4.5.0</option>
                            </select>
                            <button
                                className="notebook-create-btn"
                                onClick={handleCreateNotebook}
                                disabled={creatingNb}
                                title="Create a new empty notebook"
                            >
                                <Plus size={14} />
                                {creatingNb ? 'Creating...' : 'New'}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // Count code cells for Run All button
    const codeCellCount = safeCells.filter(c => c.cell_type === 'code').length;

    const ki = KERNEL_INFO[kernelName] || KERNEL_INFO.python3;

    return (
        <div className="notebook-viewer" ref={containerRef}>
            {/* Notebook header — two rows */}
            <div className="notebook-header">
                {/* Top row: back + name + kernel chip | add-cell buttons */}
                {/* Top row: back + name + kernel badge */}
                <div className="notebook-header-top">
                    <div className="notebook-title">
                        {onCloseNotebook && (
                            <button
                                className="notebook-back-btn"
                                onClick={onCloseNotebook}
                                title="Back to notebook list"
                            >
                                <ChevronLeft size={16} />
                            </button>
                        )}
                        <span className="notebook-name-text">{notebookName}</span>
                        <span
                            className="notebook-kernel-badge"
                            style={{ background: ki.color }}
                            title={`Kernel: ${ki.label}`}
                        >
                            {ki.badge}
                        </span>
                    </div>
                </div>

                {/* Bottom row: cell count (left) | Stop / Run All / Restart (right, all uniform) */}
                <div className="notebook-header-bottom">
                    <span className="notebook-stats">
                        {safeCells.length} {safeCells.length === 1 ? 'cell' : 'cells'}
                    </span>
                    <div className="notebook-run-controls">
                        {onStopKernel && (
                            <button
                                className="nb-ctrl-btn nb-ctrl-stop"
                                onClick={() => onStopKernel(notebookName)}
                                title="Interrupt running cell (keeps variables)"
                            >
                                <Square size={13} /><span>Stop</span>
                            </button>
                        )}
                        {onRunAll && codeCellCount > 0 && (
                            <button
                                className={clsx('nb-ctrl-btn nb-ctrl-run', { 'is-running': isRunningAll })}
                                onClick={() => onRunAll(notebookName)}
                                disabled={isRunningAll}
                                title={isRunningAll ? "Running all cells..." : `Run all ${codeCellCount} code cells`}
                            >
                                {isRunningAll
                                    ? <Clock size={13} className="animate-spin" />
                                    : <PlayCircle size={13} />
                                }
                                <span>{isRunningAll ? 'Running…' : 'Run All'}</span>
                            </button>
                        )}
                        {onRestartKernel && (
                            <button
                                className="nb-ctrl-btn nb-ctrl-restart"
                                onClick={() => onRestartKernel(notebookName)}
                                title="Restart kernel (clears all variables)"
                            >
                                <RotateCcw size={13} /><span>Restart</span>
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Cells + insertion dividers */}
            <div className="notebook-cells">
                {safeCells.length === 0 ? (
                    /* Empty notebook — single centred divider */
                    onAddCell ? (
                        <InsertCellDivider
                            notebookName={notebookName}
                            position={0}
                            onAddCell={handleAddCellWithAutoEdit}
                        />
                    ) : (
                        <div className="notebook-empty">
                            <Code size={32} className="text-muted" />
                            <p>Cells will appear here as the coder agent works</p>
                        </div>
                    )
                ) : (
                    <>
                        {/* Divider above first cell */}
                        {onAddCell && (
                            <InsertCellDivider
                                notebookName={notebookName}
                                position={0}
                                onAddCell={handleAddCellWithAutoEdit}
                            />
                        )}
                        {safeCells.map((cell, index) => (
                            <React.Fragment key={cell.id || index}>
                                <NotebookCell
                                    cell={cell}
                                    isActive={cell.id === activeCellId}
                                    notebookName={notebookName}
                                    onExecute={onExecuteCell}
                                    onUpdate={onUpdateCell}
                                    onDelete={onDeleteCell}
                                    autoEdit={cell.id === newCellId}
                                />
                                {/* Divider below each cell (insert after = index + 1) */}
                                {onAddCell && (
                                    <InsertCellDivider
                                        notebookName={notebookName}
                                        position={index + 1}
                                        onAddCell={handleAddCellWithAutoEdit}
                                    />
                                )}
                            </React.Fragment>
                        ))}
                    </>
                )}
            </div>
        </div>
    );
}

/**
 * Main NotebookViewer component with error boundary
 */
export default function NotebookViewer(props) {
    return (
        <NotebookErrorBoundary>
            <NotebookViewerInner {...props} />
        </NotebookErrorBoundary>
    );
}
