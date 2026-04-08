import React, { useState, useEffect } from 'react';
import { Database, Plus, Trash2, RefreshCw, AlertCircle, CheckCircle, Clock, FileText, Pencil, ChevronDown, ChevronUp, Settings, Zap, AlertTriangle, Loader2, CheckCircle2 } from 'lucide-react';
import config from '../../config';
import FileTreePicker from '../ui/FileTreePicker';
import './SettingsPage.css'; // Reusing settings styles

const LEGACY_EMBEDDING_MODELS = ['all-MiniLM-L6-v2', 'allenai/specter', 'allenai/specter2'];

export default function CollectionSettingsTab() {
    const [indexes, setIndexes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [creating, setCreating] = useState(false);
    const [reindexing, setReindexing] = useState({}); // { [id]: true }

    // Create Form State
    const [newIndexName, setNewIndexName] = useState("");
    const [newIndexDescription, setNewIndexDescription] = useState("");
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [showCreateModal, setShowCreateModal] = useState(false);

    // Advanced Ingestion Settings (V2-3 validated defaults)
    const [useVlm, setUseVlm] = useState(false);
    const [chunkSize, setChunkSize] = useState(512);
    const [chunkOverlap, setChunkOverlap] = useState(2);
    const [chunkingStrategy, setChunkingStrategy] = useState("simple");
    const [embeddingModel, setEmbeddingModel] = useState("BAAI/bge-m3");
    const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

    // Edit Form State
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingIndex, setEditingIndex] = useState(null);
    const [editName, setEditName] = useState("");
    const [editDescription, setEditDescription] = useState("");
    const [updating, setUpdating] = useState(false);

    // Toggle File View State
    const [openFileView, setOpenFileView] = useState(null);
    const toggleFileView = (id) => setOpenFileView(prev => prev === id ? null : id);

    useEffect(() => {
        fetchIndexes();
    }, []);

    // Smart polling: 1s when any index is active, 5s otherwise
    useEffect(() => {
        const hasActive = indexes.some(i => i.status === 'PROCESSING' || i.status === 'PENDING');
        const interval = setInterval(() => {
            fetchIndexes();
        }, hasActive ? 1000 : 5000);
        return () => clearInterval(interval);
    }, [indexes]);

    const fetchIndexes = async () => {
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/rag/indexes/`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) {
                setError(`Failed to load indexes (HTTP ${res.status})`);
                return;
            }
            const data = await res.json();
            setIndexes(data);
            setError(null);
        } catch (e) {
            console.error("Failed to fetch indexes:", e);
            setError("Cannot reach backend. Is it running?");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this index?")) return;

        try {
            const token = localStorage.getItem("mentori_token");
            if (!token) {
                alert("You are not logged in. Please refresh the page and log in again.");
                return;
            }

            const res = await fetch(`${config.API_BASE_URL}/rag/indexes/${id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (res.status === 401) {
                alert("Your session has expired. Please refresh the page and log in again.");
                return;
            }

            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(`Failed to delete index: ${errorText}`);
            }

            fetchIndexes();
        } catch (e) {
            alert(e.message);
        }
    };

    const handleReindex = async (id) => {
        if (!window.confirm("Re-index this collection? This will re-run ingestion using the original settings.")) return;

        setReindexing(prev => ({ ...prev, [id]: true }));
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/rag/indexes/${id}/reindex`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }
            fetchIndexes();
        } catch (e) {
            alert(e.message);
        } finally {
            setReindexing(prev => ({ ...prev, [id]: false }));
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();

        if (selectedFiles.length === 0) {
            alert("Please select at least one file");
            return;
        }

        setCreating(true);
        try {
            const token = localStorage.getItem("mentori_token");

            const relativePaths = selectedFiles;

            const res = await fetch(`${config.API_BASE_URL}/rag/indexes/`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: newIndexName,
                    description: newIndexDescription || null,
                    file_paths: relativePaths,
                    use_vlm: useVlm,
                    chunk_size: parseInt(chunkSize),
                    chunk_overlap: parseInt(chunkOverlap),
                    chunking_strategy: chunkingStrategy,
                    embedding_model: embeddingModel
                })
            });

            if (!res.ok) throw new Error("Failed to create index");

            // Optimistically add the new index to the table immediately (don't wait for poll)
            const newIndex = await res.json();
            setIndexes(prev => [newIndex, ...prev]);

            // Reset to validated defaults
            setShowCreateModal(false);
            setNewIndexName("");
            setNewIndexDescription("");
            setSelectedFiles([]);
            setUseVlm(false);
            setChunkSize(512);
            setChunkOverlap(2);
            setChunkingStrategy("simple");
            setEmbeddingModel("BAAI/bge-m3");
            setShowAdvancedSettings(false);
            // Also trigger a fresh fetch to confirm server state
            await fetchIndexes();
        } catch (e) {
            alert(e.message);
        } finally {
            setCreating(false);
        }
    };

    const handleEdit = (idx) => {
        setEditingIndex(idx);
        setEditName(idx.name);
        setEditDescription(idx.description || "");
        setShowEditModal(true);
    };

    const handleUpdate = async (e) => {
        e.preventDefault();
        setUpdating(true);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/rag/indexes/${editingIndex.id}`, {
                method: "PATCH",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: editName,
                    description: editDescription || null
                })
            });

            if (!res.ok) throw new Error("Failed to update index");

            setShowEditModal(false);
            setEditingIndex(null);
            fetchIndexes();
        } catch (e) {
            alert(e.message);
        } finally {
            setUpdating(false);
        }
    };

    const getStatusBadge = (status, metrics) => {
        switch (status) {
            case 'READY':
                return <span className="badge badge-success"><CheckCircle size={12} /> Ready</span>;
            case 'PROCESSING':
                if (metrics && metrics.total_files > 0) {
                    const progress = `${metrics.processed_files}/${metrics.total_files}`;
                    return (
                        <span className="badge badge-warning">
                            <RefreshCw size={12} className="spin" /> {progress} files
                        </span>
                    );
                }
                return <span className="badge badge-warning"><RefreshCw size={12} className="spin" /> Processing</span>;
            case 'PENDING':
                return <span className="badge badge-neutral"><Clock size={12} /> Pending</span>;
            case 'FAILED':
                return <span className="badge badge-error"><AlertCircle size={12} /> Failed</span>;
            default:
                return <span className="badge">{status}</span>;
        }
    };

    const renderProgressDetailRow = (idx) => {
        const metrics = idx.metrics;
        const isInit = !metrics || metrics.total_files === 0;
        const percent = isInit ? 0 : Math.round((metrics.processed_files / metrics.total_files) * 100);
        const currentFile = metrics?.current_file || 'Initializing...';
        const currentStatus = metrics?.current_file_status || 'loading';
        const isDoneFile = currentStatus === 'done';

        // Build a mini log: past files (as count) + current active file
        const processedCount = metrics?.processed_files || 0;
        const totalCount = metrics?.total_files || 0;

        return (
            <tr className="progress-detail-row">
                <td colSpan="9">
                    <div className="progress-detail-panel">
                        {/* Progress bar */}
                        {!isInit && (
                            <div className="pdp-bar-row">
                                <div className="pdp-bar-track">
                                    <div className="pdp-bar-fill" style={{ width: `${percent}%` }} />
                                </div>
                                <span className="pdp-bar-label">
                                    {processedCount}/{totalCount} files
                                    {metrics?.total_chunks > 0 && ` · ${metrics.total_chunks} chunks`}
                                    {metrics?.failed_files > 0 && (
                                        <span className="pdp-error"> · {metrics.failed_files} failed</span>
                                    )}
                                </span>
                            </div>
                        )}

                        {/* Current file log — StepCard-style */}
                        <div className="pdp-log">
                            {processedCount > 0 && (
                                <div className="pdp-log-line pdp-done">
                                    <CheckCircle2 size={12} className="pdp-icon-done" />
                                    <span>{processedCount} file{processedCount !== 1 ? 's' : ''} processed</span>
                                </div>
                            )}
                            {currentFile && !isDoneFile && (
                                <div className="pdp-log-line pdp-active">
                                    <Loader2 size={12} className="pdp-icon-spin" />
                                    <span className="pdp-file-name">{currentFile}</span>
                                    {currentStatus && currentStatus !== 'loading' && (
                                        <span className="pdp-file-status">{currentStatus}</span>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Extraction stats */}
                        {metrics && (metrics.total_figures > 0 || metrics.total_tables > 0 || metrics.total_references > 0) && (
                            <div className="pdp-extraction-stats">
                                {metrics.total_figures > 0 && <span>{metrics.total_figures} figures</span>}
                                {metrics.total_tables > 0 && <span>{metrics.total_tables} tables</span>}
                                {metrics.total_references > 0 && <span>{metrics.total_references} refs</span>}
                            </div>
                        )}
                    </div>
                </td>
            </tr>
        );
    };

    const isLegacyModel = (model) => LEGACY_EMBEDDING_MODELS.includes(model);

    const formatModelName = (model) => {
        if (!model) return 'bge-m3';
        return model.split('/').pop().substring(0, 14);
    };

    const chunkSizeUnit = chunkingStrategy === 'simple' ? 'tokens' : 'chars';

    return (
        <div className="settings-content-wrapper">
            {/* Main Card */}
            <div className="admin-card">
                <div className="card-header-row">
                    <div className="card-title">
                        <Database size={20} className="text-accent-secondary" />
                        <span>Knowledge Base (RAG Indexes)</span>
                    </div>
                    <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
                        <Plus size={16} /> New Index
                    </button>
                </div>

                <p className="card-desc">
                    Manage your custom document collections. Agents can use these indexes to answer questions with high accuracy.
                </p>

                {error && <div className="alert-error"><AlertCircle size={16} /> {error}</div>}

                {/* Index Table */}
                <div className="data-table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Description</th>
                                <th>Status</th>
                                <th>Files</th>
                                <th>Chunking</th>
                                <th>Embedding</th>
                                <th>VLM</th>
                                <th>Created</th>
                                <th style={{ width: '100px' }}></th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading && indexes.length === 0 && (
                                <tr><td colSpan="9" className="text-center">Loading indexes...</td></tr>
                            )}
                            {!loading && indexes.length === 0 && (
                                <tr><td colSpan="9" className="text-center text-muted">No indexes found. Create one to get started.</td></tr>
                            )}
                            {indexes.map(idx => (
                                <React.Fragment key={idx.id}>
                                <tr>
                                    <td className="font-medium">{idx.name}</td>
                                    <td className="text-sm text-muted" style={{ maxWidth: '200px' }}>
                                        {idx.description ? (
                                            <span title={idx.description} style={{
                                                display: '-webkit-box',
                                                WebkitLineClamp: 2,
                                                WebkitBoxOrient: 'vertical',
                                                overflow: 'hidden'
                                            }}>
                                                {idx.description}
                                            </span>
                                        ) : (
                                            <span className="text-muted" style={{ opacity: 0.5 }}>—</span>
                                        )}
                                    </td>
                                    <td>
                                        {getStatusBadge(idx.status, idx.metrics)}
                                    </td>
                                    <td>
                                        <div className="file-info-cell">
                                            <span className="file-count">{idx.file_count} files</span>
                                            <button
                                                className="btn-link"
                                                onClick={() => toggleFileView(idx.id)}
                                            >
                                                {openFileView === idx.id ? 'Hide' : 'View'}
                                            </button>
                                        </div>
                                        {openFileView === idx.id && (
                                            <div className="file-list-preview">
                                                {idx.file_paths?.map((path, i) => (
                                                    <div key={i} className="file-path-item">
                                                        <FileText size={10} /> {path.split('/').pop()}
                                                        <span className="path-tooltip">{path}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </td>
                                    <td className="text-sm">
                                        <span className="badge badge-neutral" title={`${idx.chunking_strategy || 'simple'} / ${idx.chunk_size || 512} tokens`}>
                                            {idx.chunking_strategy || 'simple'} / {idx.chunk_size || 512}
                                        </span>
                                    </td>
                                    <td className="text-sm">
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                                            <span className="badge badge-neutral" title={idx.embedding_model || 'BAAI/bge-m3'}>
                                                {formatModelName(idx.embedding_model)}
                                            </span>
                                            {isLegacyModel(idx.embedding_model) && (
                                                <span className="badge badge-warning" title="Legacy model — lower retrieval quality. Consider re-indexing with BGE-M3.">
                                                    <AlertTriangle size={10} style={{ marginRight: '3px' }} />
                                                    Legacy
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="text-sm">
                                        {idx.use_vlm || (idx.transcriber_model && idx.transcriber_model !== 'None') ? (
                                            <span className="badge badge-success" title={idx.transcriber_model}>
                                                <Zap size={10} style={{ marginRight: '3px' }} />
                                                {idx.transcriber_model && idx.transcriber_model !== 'None' ? idx.transcriber_model.split(':')[0] : 'Enabled'}
                                            </span>
                                        ) : (
                                            <span className="badge badge-neutral">Off</span>
                                        )}
                                    </td>
                                    <td className="text-sm text-muted">{new Date(idx.created_at).toLocaleDateString()}</td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '4px' }}>
                                            <button
                                                className="btn-icon"
                                                onClick={() => handleReindex(idx.id)}
                                                title="Re-index (re-run ingestion)"
                                                disabled={reindexing[idx.id] || idx.status === 'PROCESSING'}
                                            >
                                                <RefreshCw size={14} className={reindexing[idx.id] ? "spin" : ""} />
                                            </button>
                                            <button
                                                className="btn-icon"
                                                onClick={() => handleEdit(idx)}
                                                title="Edit Index"
                                            >
                                                <Pencil size={14} />
                                            </button>
                                            <button
                                                className="btn-icon danger"
                                                onClick={() => handleDelete(idx.id)}
                                                title="Delete Index"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                {(idx.status === 'PROCESSING' || idx.status === 'PENDING') && renderProgressDetailRow(idx)}
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="card-footer-actions">
                    <button className="btn-secondary" onClick={fetchIndexes} disabled={loading}>
                        <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh Status
                    </button>
                </div>
            </div>

            {/* Create Index Modal */}
            {showCreateModal && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '600px', width: '90%' }}>
                        <h3>Create New Index</h3>
                        <form onSubmit={handleCreate}>
                            <div className="form-group">
                                <label>Index Name</label>
                                <input
                                    className="form-input"
                                    value={newIndexName}
                                    onChange={(e) => setNewIndexName(e.target.value)}
                                    placeholder="e.g. Biology Research"
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label>Description <span className="text-muted">(optional)</span></label>
                                <textarea
                                    className="form-input"
                                    value={newIndexDescription}
                                    onChange={(e) => setNewIndexDescription(e.target.value)}
                                    placeholder="Describe what documents this index contains and when to use it..."
                                    rows={2}
                                    style={{ resize: 'vertical' }}
                                />
                                <small className="text-muted">
                                    Helps the AI understand when to search this index.
                                </small>
                            </div>

                            <div className="form-group">
                                <label>Select Files from Workspace</label>
                                <small className="text-muted block mb-2">
                                    Select files or folders to include in this index. Selecting a folder includes all its files.
                                </small>
                                <div className="border border-white/20 rounded p-2 bg-black/20">
                                    <FileTreePicker
                                        selectedPaths={selectedFiles}
                                        onSelectionChange={setSelectedFiles}
                                    />
                                </div>
                                {selectedFiles.length > 0 && (
                                    <small className="text-accent-secondary block mt-2">
                                        {selectedFiles.length} file(s) selected
                                    </small>
                                )}
                            </div>

                            {/* VLM Toggle */}
                            <div className="form-group">
                                <label className="toggle-label" style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
                                    <input
                                        type="checkbox"
                                        checked={useVlm}
                                        onChange={(e) => setUseVlm(e.target.checked)}
                                        style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                                    />
                                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Zap size={16} className="text-accent-secondary" />
                                        VLM-Assisted Indexing
                                    </span>
                                </label>
                                {useVlm ? (
                                    <div className="alert-warning" style={{ marginTop: '8px', padding: '8px 12px', borderRadius: '6px', fontSize: '12px' }}>
                                        <AlertCircle size={14} style={{ display: 'inline', marginRight: '6px' }} />
                                        <strong>Heads up:</strong> VLM analysis extracts figures, tables, and references but takes ~5 minutes per page.
                                    </div>
                                ) : (
                                    <small className="text-muted block" style={{ marginTop: '4px' }}>
                                        Enable to extract detailed metadata (figures, tables, references) using a Vision Language Model.
                                    </small>
                                )}
                            </div>

                            {/* Advanced Settings Toggle */}
                            <div className="form-group">
                                <button
                                    type="button"
                                    className="btn-link"
                                    onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                                    style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 0' }}
                                >
                                    <Settings size={14} />
                                    Advanced Settings
                                    {showAdvancedSettings ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                </button>

                                {showAdvancedSettings && (
                                    <div className="advanced-settings-panel" style={{
                                        marginTop: '12px',
                                        padding: '16px',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '8px',
                                        backgroundColor: 'rgba(0,0,0,0.2)'
                                    }}>
                                        {/* Chunking Strategy */}
                                        <div className="form-group" style={{ marginBottom: '12px' }}>
                                            <label style={{ fontSize: '13px' }}>Chunking Strategy</label>
                                            <select
                                                className="form-input"
                                                value={chunkingStrategy}
                                                onChange={(e) => {
                                                    setChunkingStrategy(e.target.value);
                                                    // Reset chunk size to strategy-appropriate default
                                                    setChunkSize(e.target.value === 'simple' ? 512 : 1000);
                                                }}
                                                style={{ marginTop: '4px' }}
                                            >
                                                <option value="simple">Simple — token-based sliding window (Recommended, MRR=0.988)</option>
                                                <option value="semantic">Semantic — spaCy sentence grouping (MRR=0.827)</option>
                                            </select>
                                            <small className="text-muted" style={{ fontSize: '11px' }}>
                                                Simple (token-based) outperforms semantic chunking across all tested document types.
                                            </small>
                                        </div>

                                        {/* Embedding Model */}
                                        <div className="form-group" style={{ marginBottom: '12px' }}>
                                            <label style={{ fontSize: '13px' }}>Embedding Model</label>
                                            <select
                                                className="form-input"
                                                value={embeddingModel}
                                                onChange={(e) => setEmbeddingModel(e.target.value)}
                                                style={{ marginTop: '4px' }}
                                            >
                                                <option value="BAAI/bge-m3">BAAI/bge-m3 — multilingual, 1024 dim (Recommended, MRR=0.918)</option>
                                                <option value="all-mpnet-base-v2">all-mpnet-base-v2 — general purpose, 768 dim</option>
                                                <option value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 — fast, 384 dim (Legacy)</option>
                                                <option value="allenai/specter2">allenai/specter2 — scientific, 768 dim (Not recommended — collapses at scale)</option>
                                            </select>
                                            <small className="text-muted" style={{ fontSize: '11px' }}>
                                                BGE-M3 has the best retrieval quality (V2-1 benchmark). SPECTER2 should be avoided for large collections.
                                            </small>
                                        </div>

                                        {/* Chunk Settings */}
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                            <div className="form-group" style={{ marginBottom: '0' }}>
                                                <label style={{ fontSize: '13px' }}>Chunk Size ({chunkingStrategy === 'simple' ? 'tokens' : 'chars'})</label>
                                                <input
                                                    type="number"
                                                    className="form-input"
                                                    value={chunkSize}
                                                    onChange={(e) => setChunkSize(e.target.value)}
                                                    min={chunkingStrategy === 'simple' ? 128 : 200}
                                                    max={chunkingStrategy === 'simple' ? 2048 : 4000}
                                                    step={chunkingStrategy === 'simple' ? 64 : 100}
                                                    style={{ marginTop: '4px' }}
                                                />
                                                <small className="text-muted" style={{ fontSize: '11px' }}>
                                                    {chunkingStrategy === 'simple'
                                                        ? 'Target tokens per chunk (128–2048). 512 is optimal.'
                                                        : 'Target characters per chunk (200–4000).'}
                                                </small>
                                            </div>

                                            <div className="form-group" style={{ marginBottom: '0' }}>
                                                <label style={{ fontSize: '13px' }}>Overlap (sentences)</label>
                                                <input
                                                    type="number"
                                                    className="form-input"
                                                    value={chunkOverlap}
                                                    onChange={(e) => setChunkOverlap(e.target.value)}
                                                    min={0}
                                                    max={5}
                                                    style={{ marginTop: '4px' }}
                                                />
                                                <small className="text-muted" style={{ fontSize: '11px' }}>
                                                    Sentences shared between chunks (0–5).
                                                </small>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
                                <button type="submit" className="btn-primary" disabled={creating || selectedFiles.length === 0}>
                                    {creating ? "Creating Index..." : "Create Index"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Edit Index Modal */}
            {showEditModal && editingIndex && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '500px', width: '90%' }}>
                        <h3>Edit Index</h3>
                        <form onSubmit={handleUpdate}>
                            <div className="form-group">
                                <label>Index Name</label>
                                <input
                                    className="form-input"
                                    value={editName}
                                    onChange={(e) => setEditName(e.target.value)}
                                    placeholder="e.g. Biology Research"
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label>Description <span className="text-muted">(optional)</span></label>
                                <textarea
                                    className="form-input"
                                    value={editDescription}
                                    onChange={(e) => setEditDescription(e.target.value)}
                                    placeholder="Describe what documents this index contains and when to use it..."
                                    rows={3}
                                    style={{ resize: 'vertical' }}
                                />
                                <small className="text-muted">
                                    Helps the AI understand when to search this index.
                                </small>
                            </div>

                            <div className="form-group">
                                <label className="text-muted">
                                    Chunking: {editingIndex.chunking_strategy || 'simple'} / {editingIndex.chunk_size || 512} {editingIndex.chunking_strategy === 'semantic' ? 'chars' : 'tokens'} &nbsp;•&nbsp;
                                    Embedding: {editingIndex.embedding_model || 'BAAI/bge-m3'} &nbsp;•&nbsp;
                                    Files: {editingIndex.file_count}
                                </label>
                                <small className="text-muted block">
                                    Ingestion settings and files cannot be changed after creation. Use Re-index to re-run ingestion with the same settings.
                                </small>
                            </div>

                            <div className="modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setShowEditModal(false)}>Cancel</button>
                                <button type="submit" className="btn-primary" disabled={updating}>
                                    {updating ? "Saving..." : "Save Changes"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
