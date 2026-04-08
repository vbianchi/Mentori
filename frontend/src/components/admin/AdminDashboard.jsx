import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    X, RefreshCw, LogOut, Lock, Key, Check, ChevronLeft, ShieldCheck, Cpu,
    Search, FileText, Activity, Edit2, Users, Database, Plus, Shield, Trash2, Download,
    Bot, Server, Upload, Zap, Save, BarChart3, Wrench, ToggleLeft, ToggleRight, AlertTriangle
} from 'lucide-react';
import config from '../../config';
import './AdminDashboard.css';

export default function AdminDashboard() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('users');
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Create User Form State
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newUserEmail, setNewUserEmail] = useState("");
    const [newUserPassword, setNewUserPassword] = useState("");
    const [newUserRole, setNewUserRole] = useState("user");

    // Change Password Form State
    const [oldPassword, setOldPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [pwMsg, setPwMsg] = useState(null);
    const [pwError, setPwError] = useState(null);

    // Models State
    const [models, setModels] = useState([]);
    const [syncingModels, setSyncingModels] = useState(false);
    const [modelProviderFilter, setModelProviderFilter] = useState('ALL');

    // User Search & Edit
    const [searchQuery, setSearchQuery] = useState("");
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingUser, setEditingUser] = useState(null);
    const [editEmail, setEditEmail] = useState("");
    const [editRole, setEditRole] = useState("user");
    const [editPassword, setEditPassword] = useState(""); // Optional reset

    // System Stats & Logs
    const [logs, setLogs] = useState([]);
    const [systemStats, setSystemStats] = useState(null);

    // Admin Agent Roles State
    const [adminRoles, setAdminRoles] = useState({});
    const [adminRolesLoading, setAdminRolesLoading] = useState(false);
    const [pushingRole, setPushingRole] = useState(null);

    // Ollama Management State
    const [ollamaStatus, setOllamaStatus] = useState(null);
    const [preloadList, setPreloadList] = useState([]);
    const [modelPolicy, setModelPolicy] = useState('any');
    const [selectedModelToPreload, setSelectedModelToPreload] = useState('');
    const [preloading, setPreloading] = useState(false);
    const [preloadResults, setPreloadResults] = useState(null);
    const [keepAliveOption, setKeepAliveOption] = useState('-1');

    // Context Window Setting
    const [minContextWindow, setMinContextWindow] = useState(131072);
    const [contextWindowSaving, setContextWindowSaving] = useState(false);

    // Telemetry State
    const [telemetrySummary, setTelemetrySummary] = useState(null);
    const [telemetryTimeline, setTelemetryTimeline] = useState([]);
    const [telemetryLoading, setTelemetryLoading] = useState(false);

    // MCP Tools State
    const [mcpTools, setMcpTools] = useState([]);
    const [mcpToolsLoading, setMcpToolsLoading] = useState(false);
    const [mcpToolsCategoryFilter, setMcpToolsCategoryFilter] = useState('all');
    const [togglingTool, setTogglingTool] = useState(null);
    const [pendingRestartTools, setPendingRestartTools] = useState(new Set());

    // Agent role definitions for display
    const AGENT_ROLES_CONFIG = [
        { key: 'lead_researcher', label: 'Lead Researcher', sub: 'Main orchestrator', colorClass: 'text-purple-400' },
        { key: 'supervisor', label: 'Supervisor', sub: 'Quality evaluation', colorClass: 'text-yellow-400' },
        { key: 'librarian', label: 'Librarian', sub: 'Memory consolidation', colorClass: 'text-blue-400' },
        { key: 'coder', label: 'Coder', sub: 'Code execution', colorClass: 'text-green-400' },
        { key: 'handyman', label: 'Handyman', sub: 'Tool execution', colorClass: 'text-orange-400' },
        { key: 'editor', label: 'Editor', sub: 'Writing & summarizing', colorClass: 'text-pink-400' },
        { key: 'transcriber', label: 'Transcriber', sub: 'OCR processing', colorClass: 'text-cyan-400' },
        { key: 'vision', label: 'Vision', sub: 'Image analysis', colorClass: 'text-indigo-400' },
        { key: 'default', label: 'Default', sub: 'Fallback model', colorClass: 'text-gray-400' },
    ];

    const loadUsers = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/users`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Failed to load users");
            const data = await res.json();
            setUsers(data);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'users') loadUsers();
        if (activeTab === 'models') loadModels();
        if (activeTab === 'logs') loadLogs();
        if (activeTab === 'system') loadSystemStats();
        if (activeTab === 'agent-roles') { loadAdminRoles(); loadModels(); loadContextWindow(); }
        if (activeTab === 'ollama') { loadOllamaStatus(); loadPreloadList(); loadModels(); }
        if (activeTab === 'telemetry') loadTelemetry();
        if (activeTab === 'tools') loadMcpTools();
    }, [activeTab]);

    const loadLogs = async () => {
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/system/logs?lines=200`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) setLogs(await res.json());
        } catch (e) {
            console.error("Failed to load logs", e);
        }
    };

    const loadSystemStats = async () => {
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/system/stats`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) setSystemStats(await res.json());
        } catch (e) {
            console.error("Failed to load stats", e);
        }
    };

    const loadMcpTools = async () => {
        setMcpToolsLoading(true);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/tools`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) setMcpTools(await res.json());
        } catch (e) {
            console.error("Failed to load MCP tools", e);
        } finally {
            setMcpToolsLoading(false);
        }
    };

    const handleToggleTool = async (toolName, currentEnabled) => {
        setTogglingTool(toolName);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/tools/${toolName}/enabled`, {
                method: "PUT",
                headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
                body: JSON.stringify({ enabled: !currentEnabled }),
            });
            if (!res.ok) throw new Error("Failed to update tool");
            // Update local state immediately
            setMcpTools(prev => prev.map(t =>
                t.name === toolName ? { ...t, enabled: !currentEnabled } : t
            ));
            // Track that this tool needs a restart to take effect
            setPendingRestartTools(prev => new Set([...prev, toolName]));
        } catch (e) {
            alert(e.message);
        } finally {
            setTogglingTool(null);
        }
    };

    const handleRefreshTools = async () => {
        setMcpToolsLoading(true);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/tools/refresh`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                alert(`Tools refreshed. ${data.tool_count} tools discovered.`);
                loadMcpTools();
            }
        } catch (e) {
            console.error("Failed to refresh tools", e);
        } finally {
            setMcpToolsLoading(false);
        }
    };

    const loadTelemetry = async () => {
        setTelemetryLoading(true);
        try {
            const token = localStorage.getItem("mentori_token");
            const [summaryRes, timelineRes] = await Promise.all([
                fetch(`${config.API_BASE_URL}/admin/telemetry/summary`, {
                    headers: { "Authorization": `Bearer ${token}` }
                }),
                fetch(`${config.API_BASE_URL}/admin/telemetry/timeline?days=30`, {
                    headers: { "Authorization": `Bearer ${token}` }
                }),
            ]);
            if (summaryRes.ok) setTelemetrySummary(await summaryRes.json());
            if (timelineRes.ok) setTelemetryTimeline(await timelineRes.json());
        } catch (e) {
            console.error("Failed to load telemetry", e);
        } finally {
            setTelemetryLoading(false);
        }
    };

    const loadModels = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/models/config`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Failed to load models");
            const data = await res.json();
            setModels(data);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSyncModels = async (force = false) => {
        setSyncingModels(true);
        try {
            const token = localStorage.getItem("mentori_token");
            const url = `${config.API_BASE_URL}/admin/models/sync${force ? '?force=true' : ''}`;
            const res = await fetch(url, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Failed to sync models");
            const result = await res.json();
            const msg = force
                ? `Force sync done. Added: ${result.added}, Re-checked: ${result.updated}, Total: ${result.total_live}`
                : `Sync done. New models added: ${result.added}, Total: ${result.total_live}`;
            alert(msg);
            loadModels();
        } catch (e) {
            alert(e.message);
        } finally {
            setSyncingModels(false);
        }
    };

    const handleToggleModel = async (id, currentStatus) => {
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/models/${id}`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ enabled: !currentStatus })
            });
            if (!res.ok) throw new Error("Failed to update model");
            loadModels();
        } catch (e) {
            alert(e.message);
        }
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/users`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: newUserEmail,
                    password: newUserPassword,
                    role: newUserRole
                })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to create user");
            }

            setShowCreateModal(false);
            setNewUserEmail("");
            setNewUserPassword("");
            loadUsers();
        } catch (e) {
            alert(e.message);
        }
    };

    const handleDeleteUser = async (userId) => {
        if (!confirm("Are you sure you want to delete this user? This cannot be undone.")) return;
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/users/${userId}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Failed to delete user");
            loadUsers();
        } catch (e) {
            alert(e.message);
        }
    };

    const handlePromoteUser = async (userId) => {
        if (!confirm("Promote this user to Admin?")) return;
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/users/${userId}/role?role=admin`, {
                method: "PUT",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Failed to update role");
            loadUsers();
        } catch (e) {
            alert(e.message);
        }
    };

    const prepareEditUser = (user) => {
        setEditingUser(user);
        setEditEmail(user.email);
        setEditRole(user.role);
        setEditPassword(""); // Reset, empty means no change
        setShowEditModal(true);
    };

    const handleUpdateUser = async (e) => {
        e.preventDefault();
        try {
            const token = localStorage.getItem("mentori_token");
            const payload = { role: editRole };
            if (editEmail !== editingUser.email) payload.email = editEmail;
            if (editPassword) payload.password = editPassword;

            const res = await fetch(`${config.API_BASE_URL}/admin/users/${editingUser.id}`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to update user");
            }

            setShowEditModal(false);
            setEditingUser(null);
            loadUsers();
        } catch (e) {
            alert(e.message);
        }
    };

    const handleExport = async () => {
        const token = localStorage.getItem("mentori_token");
        window.open(`${config.API_BASE_URL}/admin/export?token=${token}`, '_blank');
        // Note: Bearer token in URL is not standard, normally requires fetch blob. 
        // For now using the fetch approach for better Auth header handling if needed, 
        // but window.open is easiest for download if endpoint allows query param auth or cookie. 
        // The current backend endpoint expects Header. 
        // Let's implement Blob download.

        try {
            const res = await fetch(`${config.API_BASE_URL}/admin/export`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Export failed");

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `mentori_export_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (e) {
            alert("Export failed: " + e.message);
        }
    };

    const handleChangePassword = async (e) => {
        e.preventDefault();
        setPwMsg(null);
        setPwError(null);

        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/auth/change-password`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    old_password: oldPassword,
                    new_password: newPassword
                })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to update password");
            }

            setPwMsg("Password updated successfully!");
            setOldPassword("");
            setNewPassword("");
        } catch (e) {
            setPwError(e.message);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("mentori_token");
        navigate('/login');
    };

    // ============================================================
    // Admin Agent Roles Functions
    // ============================================================

    const loadAdminRoles = async () => {
        setAdminRolesLoading(true);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/agent-roles`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setAdminRoles(data.roles || {});
            }
        } catch (e) {
            console.error("Failed to load admin roles", e);
        } finally {
            setAdminRolesLoading(false);
        }
    };

    const loadContextWindow = async () => {
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/context-window`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setMinContextWindow(data.tokens);
            }
        } catch (e) {
            console.error("Failed to load context window setting", e);
        }
    };

    const handleSaveContextWindow = async () => {
        setContextWindowSaving(true);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/context-window`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ tokens: Number(minContextWindow) })
            });
            if (!res.ok) throw new Error("Failed to save");
        } catch (e) {
            console.error("Failed to save context window setting", e);
        } finally {
            setContextWindowSaving(false);
        }
    };

    const handleRoleChange = (role, model) => {
        setAdminRoles(prev => ({ ...prev, [role]: model }));
    };

    const handleSaveAdminRoles = async () => {
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/agent-roles`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ roles: adminRoles })
            });
            if (res.ok) {
                alert("Admin agent roles saved successfully!");
            } else {
                throw new Error("Failed to save");
            }
        } catch (e) {
            alert("Error saving admin roles: " + e.message);
        }
    };

    const handlePushRole = async (role) => {
        const model = adminRoles[role];
        if (!model) {
            alert("Please select a model for this role first");
            return;
        }
        if (!confirm(`Push "${model}" to ALL users for the ${role} role? This will overwrite their current setting.`)) {
            return;
        }

        setPushingRole(role);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/agent-roles/push`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ role, model })
            });
            if (res.ok) {
                const data = await res.json();
                alert(`Successfully pushed to ${data.affected_users} users!`);
            } else {
                throw new Error("Failed to push");
            }
        } catch (e) {
            alert("Error pushing role: " + e.message);
        } finally {
            setPushingRole(null);
        }
    };

    const handleClearRole = async (role) => {
        if (!confirm(`Clear the ${role} role from ALL users? They will fall back to their default model.`)) {
            return;
        }

        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/agent-roles/clear`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ role })
            });
            if (res.ok) {
                const data = await res.json();
                alert(`Cleared from ${data.affected_users} users!`);
                setAdminRoles(prev => ({ ...prev, [role]: '' }));
            } else {
                throw new Error("Failed to clear");
            }
        } catch (e) {
            alert("Error clearing role: " + e.message);
        }
    };

    // ============================================================
    // Ollama Management Functions
    // ============================================================

    const loadOllamaStatus = async () => {
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/ollama/status`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                setOllamaStatus(await res.json());
            }
        } catch (e) {
            console.error("Failed to load Ollama status", e);
        }
    };

    const loadPreloadList = async () => {
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/ollama/preload-list`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setPreloadList(data.models || []);
                setModelPolicy(data.policy || 'any');
            }
        } catch (e) {
            console.error("Failed to load preload list", e);
        }
    };

    const handleAddToPreload = () => {
        if (!selectedModelToPreload) return;
        if (!preloadList.includes(selectedModelToPreload)) {
            setPreloadList(prev => [...prev, selectedModelToPreload]);
        }
        setSelectedModelToPreload('');
    };

    const handleRemoveFromPreload = (model) => {
        setPreloadList(prev => prev.filter(m => m !== model));
    };

    const handleSavePreloadConfig = async () => {
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/ollama/preload-list`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ models: preloadList, policy: modelPolicy })
            });
            if (res.ok) {
                alert("Preload configuration saved!");
            } else {
                throw new Error("Failed to save");
            }
        } catch (e) {
            alert("Error saving preload config: " + e.message);
        }
    };

    const handlePreloadNow = async (keepAliveValue = "-1") => {
        if (preloadList.length === 0) {
            alert("No models in preload list");
            return;
        }

        setPreloading(true);
        setPreloadResults(null);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/ollama/preload`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ models: preloadList, keep_alive: keepAliveValue })
            });
            const data = await res.json();
            if (res.ok) {
                setPreloadResults(data.results || []);
                loadOllamaStatus();
            } else {
                const errMsg = data?.detail || data?.error || `HTTP ${res.status}`;
                throw new Error(errMsg);
            }
        } catch (e) {
            alert("Preload error: " + e.message);
        } finally {
            setPreloading(false);
        }
    };

    const handleUnloadModel = async (model) => {
        if (!confirm(`Unload ${model} from memory?`)) return;

        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/admin/ollama/unload`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ model })
            });
            if (res.ok) {
                loadOllamaStatus();
            }
        } catch (e) {
            alert("Error unloading: " + e.message);
        }
    };

    const formatBytes = (bytes) => {
        if (!bytes) return 'N/A';
        const gb = bytes / (1024 ** 3);
        return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(bytes / (1024 ** 2)).toFixed(0)} MB`;
    };

    const formatExpiry = (expiresAt) => {
        if (!expiresAt) return 'Never';
        const date = new Date(expiresAt);
        return date.toLocaleTimeString();
    };

    return (
        <div className="admin-container">
            <header className="admin-header">
                <div className="admin-brand">
                    <ShieldCheck size={24} className="text-accent-primary" />
                    <span>Admin Console</span>
                </div>

                <nav className="admin-nav">
                    <button
                        className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
                        onClick={() => setActiveTab('users')}
                    >
                        <Users size={16} /> Users
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'models' ? 'active' : ''}`}
                        onClick={() => setActiveTab('models')}
                    >
                        <Cpu size={16} /> Models
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'agent-roles' ? 'active' : ''}`}
                        onClick={() => setActiveTab('agent-roles')}
                    >
                        <Bot size={16} /> Agent Roles
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'ollama' ? 'active' : ''}`}
                        onClick={() => setActiveTab('ollama')}
                    >
                        <Server size={16} /> Ollama
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'data' ? 'active' : ''}`}
                        onClick={() => setActiveTab('data')}
                    >
                        <Database size={16} /> Data Management
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'security' ? 'active' : ''}`}
                        onClick={() => setActiveTab('security')}
                    >
                        <Lock size={16} /> Security
                    </button>

                    <button
                        className={`admin-tab ${activeTab === 'tools' ? 'active' : ''}`}
                        onClick={() => setActiveTab('tools')}
                    >
                        <Wrench size={16} /> Tools
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'telemetry' ? 'active' : ''}`}
                        onClick={() => setActiveTab('telemetry')}
                    >
                        <BarChart3 size={16} /> Telemetry
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'logs' ? 'active' : ''}`}
                        onClick={() => setActiveTab('logs')}
                    >
                        <FileText size={16} /> Logs
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'system' ? 'active' : ''}`}
                        onClick={() => setActiveTab('system')}
                    >
                        <Activity size={16} /> System
                    </button>
                </nav>

                <div className="admin-actions">
                    <button onClick={() => navigate('/')} className="btn-header">
                        <ChevronLeft size={16} /> Back to App
                    </button>
                    <button onClick={handleLogout} className="btn-header" title="Logout">
                        <LogOut size={16} />
                    </button>
                </div>
            </header>

            <main className="admin-content">
                {/* USERS TAB */}
                {activeTab === 'users' && (
                    <div className="space-y-4">
                        <div className="user-mgmt-header">
                            <h2 className="text-xl font-semibold text-white">User Management</h2>
                            <div className="user-mgmt-actions">
                                <div className="search-container">
                                    <Search size={16} className="search-icon" />
                                    <input
                                        type="text"
                                        placeholder="Search users..."
                                        className="search-input"
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                    />
                                </div>
                                <button onClick={() => setShowCreateModal(true)} className="btn-primary">
                                    <Plus size={16} /> Add User
                                </button>
                            </div>
                        </div>

                        {error && (
                            <div className="p-4 mb-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg flex items-center gap-2">
                                <X size={16} />
                                <span>Error loading users: {error}</span>
                            </div>
                        )}

                        <div className="admin-table-container">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Email</th>
                                        <th>Role</th>
                                        <th>Joined</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {users.filter(u => u.email.toLowerCase().includes(searchQuery.toLowerCase()) || u.id.includes(searchQuery)).map(u => (
                                        <tr key={u.id}>
                                            <td className="font-mono text-xs text-dim">#{u.id}</td>
                                            <td className="text-white">{u.email}</td>
                                            <td>
                                                <span className={`role-badge ${u.role}`}>
                                                    {u.role}
                                                </span>
                                            </td>
                                            <td>{new Date(u.created_at).toLocaleDateString()}</td>
                                            <td>
                                                <div className="admin-actions">
                                                    {u.role !== 'admin' && (
                                                        <button
                                                            className="action-btn promote"
                                                            title="Promote to Admin"
                                                            onClick={() => handlePromoteUser(u.id)}
                                                        >
                                                            <Shield size={16} />
                                                        </button>
                                                    )}
                                                    <button
                                                        className="action-btn"
                                                        title="Edit User"
                                                        onClick={() => prepareEditUser(u)}
                                                    >
                                                        <Edit2 size={16} />
                                                    </button>
                                                    <button
                                                        className="action-btn danger"
                                                        title="Delete User"
                                                        onClick={() => handleDeleteUser(u.id)}
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                    {users.length === 0 && !loading && (
                                        <tr>
                                            <td colSpan="5" className="text-center py-8 text-dim">No users found</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* MODELS TAB */}
                {activeTab === 'models' && (
                    <div className="space-y-4">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-semibold text-white">Model Management</h2>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <button onClick={() => handleSyncModels(false)} className="btn-primary" disabled={syncingModels} title="Add new models only (fast)">
                                    <RefreshCw size={16} className={syncingModels ? 'animate-spin' : ''} />
                                    {syncingModels ? 'Syncing...' : 'Sync Models'}
                                </button>
                                <button onClick={() => handleSyncModels(true)} className="btn-secondary" disabled={syncingModels} title="Re-probe all models for thinking capabilities (slow)">
                                    <RefreshCw size={14} />
                                    Force Re-check
                                </button>
                            </div>
                        </div>

                        {/* Provider Filters */}
                        <div className="filter-pills mb-4">
                            {['ALL', 'OLLAMA', 'GEMINI', 'OPENAI', 'CLAUDE'].map(provider => (
                                <button
                                    key={provider}
                                    onClick={() => setModelProviderFilter(provider)}
                                    className={`filter-pill ${modelProviderFilter === provider ? 'active' : ''}`}
                                >
                                    {provider === 'ALL' ? 'All Providers' : provider}
                                </button>
                            ))}
                        </div>

                        <div className="admin-table-container">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>Provider</th>
                                        <th>Model Name</th>
                                        <th>Status</th>
                                        <th>Thinking</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {models
                                        .filter(m => modelProviderFilter === 'ALL' || m.provider.toUpperCase() === modelProviderFilter)
                                        .map(m => (
                                            <tr key={m.id}>
                                                <td className="text-dim uppercase text-xs font-bold">{m.provider}</td>
                                                <td className="text-white font-mono">{m.model_identifier.split("::")[1]}</td>
                                                <td>
                                                    <span className={`role-badge ${m.enabled ? 'admin' : 'user'}`}>
                                                        {m.enabled ? 'Enabled' : 'Disabled'}
                                                    </span>
                                                </td>
                                                <td>
                                                    {m.supports_thinking ? (
                                                        <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded flex items-center gap-1 w-fit">
                                                            <Cpu size={12} /> Thinking
                                                        </span>
                                                    ) : (
                                                        <span className="text-xs text-dim opacity-50">No</span>
                                                    )}
                                                </td>
                                                <td>
                                                    <button
                                                        onClick={() => handleToggleModel(m.id, m.enabled)}
                                                        className={`px-3 py-1 rounded text-xs font-medium border ${m.enabled ? 'border-red-500/50 text-red-400 hover:bg-red-500/10' : 'border-green-500/50 text-green-400 hover:bg-green-500/10'}`}
                                                    >
                                                        {m.enabled ? 'Disable' : 'Enable'}
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    {models.filter(m => modelProviderFilter === 'ALL' || m.provider.toUpperCase() === modelProviderFilter).length === 0 && !loading && (
                                        <tr>
                                            <td colSpan="4" className="text-center py-8 text-dim">
                                                No models found for {modelProviderFilter}.
                                                {modelProviderFilter === 'GEMINI' && " (Hint: Check your API Key in Settings)"}
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )
                }

                {/* AGENT ROLES TAB */}
                {activeTab === 'agent-roles' && (
                    <div className="space-y-4">
                        <div className="user-mgmt-header">
                            <h2 className="text-xl font-semibold text-white">Admin Agent Roles</h2>
                            <p className="text-sm text-dim mt-1">
                                Configure recommended models for each agent role. Use "Push to All" to apply to all users.
                            </p>
                        </div>

                        <div className="admin-table-container">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>Agent Role</th>
                                        <th>Recommended Model</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {AGENT_ROLES_CONFIG.map(role => (
                                        <tr key={role.key}>
                                            <td>
                                                <span className={`font-medium ${role.colorClass}`}>
                                                    {role.label}
                                                </span>
                                                <p className="text-xs text-dim">{role.sub}</p>
                                            </td>
                                            <td>
                                                <select
                                                    value={adminRoles[role.key] || ''}
                                                    onChange={(e) => handleRoleChange(role.key, e.target.value)}
                                                    className="form-input text-sm"
                                                    style={{ minWidth: '250px' }}
                                                >
                                                    <option value="">Not Set</option>
                                                    {models.filter(m => m.enabled).map(m => (
                                                        <option key={m.id} value={m.model_identifier}>
                                                            {m.model_identifier}
                                                        </option>
                                                    ))}
                                                </select>
                                            </td>
                                            <td>
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => handlePushRole(role.key)}
                                                        className="px-3 py-1 text-xs font-medium bg-purple-500/20 text-purple-300 rounded border border-purple-500/30 hover:bg-purple-500/30 flex items-center gap-1 disabled:opacity-50"
                                                        disabled={!adminRoles[role.key] || pushingRole === role.key}
                                                    >
                                                        <Upload size={12} />
                                                        {pushingRole === role.key ? 'Pushing...' : 'Push to All'}
                                                    </button>
                                                    <button
                                                        onClick={() => handleClearRole(role.key)}
                                                        className="px-3 py-1 text-xs font-medium bg-red-500/10 text-red-400 rounded border border-red-500/20 hover:bg-red-500/20"
                                                        title="Clear from all users"
                                                    >
                                                        <Trash2 size={12} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        <button onClick={handleSaveAdminRoles} className="btn-primary">
                            <Save size={16} /> Save Configuration
                        </button>

                        {/* Context Window Setting */}
                        <div className="admin-card mt-6">
                            <div className="card-title">
                                <Cpu size={20} className="text-accent-secondary" />
                                <h3 className="text-lg font-semibold text-white">Minimum Context Window</h3>
                            </div>
                            <p className="text-sm text-dim mb-4">
                                Set this to the <strong className="text-white">smallest context window</strong> among
                                models deployed for the <span className="text-purple-400">Lead Researcher</span>,{' '}
                                <span className="text-pink-400">Editor</span>, and{' '}
                                <span className="text-yellow-400">Supervisor</span> roles.
                                Mentori uses this value to dynamically size synthesis prompts and decide when to
                                compress large tool outputs — so the system always stays within model limits without
                                wasting capacity on smaller, unnecessary truncations.
                            </p>
                            <p className="text-xs text-dim mb-4">
                                Common values: gpt-oss:20b = 128K · deepseek-R1 = 128K · qwen3:30b = 256K ·
                                llama4 = 10M · gemini-flash = 1M. Default: 131,072 (128K tokens).
                            </p>
                            <div className="flex items-center gap-3">
                                <input
                                    type="number"
                                    value={minContextWindow}
                                    onChange={(e) => setMinContextWindow(Math.max(4096, parseInt(e.target.value) || 4096))}
                                    min={4096}
                                    step={4096}
                                    className="form-input text-sm"
                                    style={{ width: '180px' }}
                                />
                                <span className="text-sm text-dim">tokens</span>
                                <span className="text-xs text-dim">
                                    (≈ {Math.round(minContextWindow / 1000)}K · distiller fires above{' '}
                                    {Math.round(minContextWindow * 0.40 / 1000)}K tokens per step)
                                </span>
                                <button
                                    onClick={handleSaveContextWindow}
                                    disabled={contextWindowSaving}
                                    className="btn-primary ml-auto"
                                >
                                    <Save size={14} />
                                    {contextWindowSaving ? 'Saving...' : 'Save'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* OLLAMA TAB */}
                {activeTab === 'ollama' && (
                    <div className="space-y-6">
                        {/* Concurrency Settings Card */}
                        <div className="admin-card">
                            <div className="card-title">
                                <Cpu size={20} className="text-accent-secondary" />
                                <span>Concurrency Settings</span>
                            </div>
                            <p className="card-desc">
                                Read from Ollama environment variables — restart Ollama to apply changes. These three settings determine how many users Mentori can serve simultaneously.
                            </p>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                                <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                                    <div className="text-xs text-dim mb-1">OLLAMA_NUM_PARALLEL</div>
                                    <div className="text-xl font-semibold text-white">
                                        {ollamaStatus?.concurrency?.num_parallel || '1 (default)'}
                                    </div>
                                    <div className="text-xs text-dim mt-2">
                                        Simultaneous requests one model handles. Set ≥ expected concurrent users. Higher values use more VRAM.
                                    </div>
                                </div>
                                <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                                    <div className="text-xs text-dim mb-1">OLLAMA_MAX_LOADED_MODELS</div>
                                    <div className="text-xl font-semibold text-white">
                                        {ollamaStatus?.concurrency?.max_loaded_models || '3 (default)'}
                                    </div>
                                    <div className="text-xs text-dim mt-2">
                                        Models kept in GPU memory at once. When exceeded, least-recently-used models are swapped to disk (adds latency).
                                    </div>
                                </div>
                                <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                                    <div className="text-xs text-dim mb-1">OLLAMA_KEEP_ALIVE</div>
                                    <div className="text-xl font-semibold text-white">
                                        {ollamaStatus?.concurrency?.keep_alive || '5m (default)'}
                                    </div>
                                    <div className="text-xs text-dim mt-2">
                                        Idle timeout before a model unloads. Use Preload Config with ∞ to keep primary models always resident.
                                    </div>
                                </div>
                            </div>

                            <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 text-blue-300 rounded-lg text-sm">
                                <strong>Sizing guide:</strong> To support N simultaneous users — set <code>OLLAMA_NUM_PARALLEL ≥ N</code> and preload your primary models so they stay resident between requests. Each parallel slot roughly doubles the VRAM footprint of that model.
                            </div>

                            {!ollamaStatus?.ollama_available && (
                                <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm">
                                    Ollama is not available at {ollamaStatus?.base_url || 'unknown'}
                                </div>
                            )}
                        </div>

                        {/* Live Status Card */}
                        <div className="admin-card">
                            <div className="card-title flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                    <Activity size={20} className="text-green-400" />
                                    <span>Currently Loaded Models</span>
                                </div>
                                <button onClick={loadOllamaStatus} className="btn-secondary text-xs">
                                    <RefreshCw size={12} /> Refresh
                                </button>
                            </div>

                            <div className="admin-table-container mt-4">
                                <table className="admin-table">
                                    <thead>
                                        <tr>
                                            <th>Model</th>
                                            <th>Size</th>
                                            <th>VRAM</th>
                                            <th>Expires</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {ollamaStatus?.loaded_models?.length > 0 ? (
                                            ollamaStatus.loaded_models.map((m, idx) => (
                                                <tr key={idx}>
                                                    <td className="font-mono text-white">{m.model || m.name}</td>
                                                    <td>{formatBytes(m.size)}</td>
                                                    <td>{formatBytes(m.size_vram)}</td>
                                                    <td>{formatExpiry(m.expires_at)}</td>
                                                    <td>
                                                        <button
                                                            onClick={() => handleUnloadModel(m.model || m.name)}
                                                            className="action-btn danger"
                                                            title="Unload model"
                                                        >
                                                            <X size={14} />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="5" className="text-center py-8 text-dim">
                                                    No models currently loaded
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Preload Configuration Card */}
                        <div className="admin-card">
                            <div className="card-title">
                                <Database size={20} className="text-purple-400" />
                                <span>Preload Configuration</span>
                            </div>
                            <p className="card-desc">
                                Models below are loaded into Ollama memory on startup and kept resident. Use this to eliminate cold-start delays for your primary models.
                            </p>

                            {/* Preload Model List */}
                            <div className="space-y-2 mt-4">
                                {preloadList.length === 0 && (
                                    <div className="text-dim text-sm py-3 text-center border border-dashed border-white/10 rounded-lg">
                                        No models configured — add one below
                                    </div>
                                )}
                                {preloadList.map(model => {
                                    const name = model.includes('::') ? model.split('::')[1] : model;
                                    const result = preloadResults?.find(r => r.model === name);
                                    return (
                                        <div key={model} className="flex items-center justify-between px-3 py-2 bg-white/5 rounded-lg border border-white/10">
                                            <span className="font-mono text-sm text-white">{name}</span>
                                            <div className="flex items-center gap-2">
                                                {result && (
                                                    <span className={`text-xs px-2 py-0.5 rounded-full ${result.status === 'loaded' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                                        {result.status === 'loaded' ? '✓ loaded' : `✗ ${result.error || 'failed'}`}
                                                    </span>
                                                )}
                                                <button onClick={() => handleRemoveFromPreload(model)} className="text-muted hover:text-red-400 transition-colors" title="Remove">
                                                    <X size={14} />
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Add Model Row */}
                            <div className="flex gap-2 mt-3">
                                <select
                                    value={selectedModelToPreload}
                                    onChange={(e) => setSelectedModelToPreload(e.target.value)}
                                    className="form-input flex-1"
                                >
                                    <option value="">+ Add model to preload list...</option>
                                    {models
                                        .filter(m => m.enabled && !preloadList.includes(m.model_identifier))
                                        .map(m => (
                                            <option key={m.id} value={m.model_identifier}>
                                                {m.model_identifier.includes('::') ? m.model_identifier.split('::')[1] : m.model_identifier}
                                            </option>
                                        ))}
                                </select>
                                <button onClick={handleAddToPreload} className="btn-secondary" disabled={!selectedModelToPreload}>
                                    <Plus size={14} /> Add
                                </button>
                            </div>

                            {/* User Model Policy */}
                            <div className="mt-5 p-4 bg-[#1e1e1e] rounded-lg border border-white/5">
                                <h4 className="text-white font-medium mb-2 text-sm">User Model Policy</h4>
                                <select
                                    value={modelPolicy}
                                    onChange={(e) => setModelPolicy(e.target.value)}
                                    className="form-input"
                                >
                                    <option value="any">Any Model — users can select any enabled model</option>
                                    <option value="preloaded_only">Preloaded Only — restrict to preloaded models</option>
                                    <option value="admin_approved">Admin Approved — only admin-enabled models</option>
                                </select>
                                <p className="text-xs text-dim mt-2">
                                    Use "Preloaded Only" on VRAM-constrained systems to prevent model swapping during user sessions.
                                </p>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex items-center gap-3 mt-4 flex-wrap">
                                <button onClick={handleSavePreloadConfig} className="btn-primary">
                                    <Save size={14} /> Save Configuration
                                </button>
                                <div className="flex items-center gap-2">
                                    <select
                                        value={keepAliveOption}
                                        onChange={e => setKeepAliveOption(e.target.value)}
                                        className="form-input text-sm"
                                        style={{ width: 'auto', padding: '0.3rem 0.6rem' }}
                                        title="How long to keep models loaded"
                                    >
                                        <option value="-1">∞ Keep forever</option>
                                        <option value="4h">4 hours</option>
                                        <option value="1h">1 hour</option>
                                        <option value="30m">30 minutes</option>
                                    </select>
                                    <button
                                        onClick={() => handlePreloadNow(keepAliveOption)}
                                        className="btn-secondary"
                                        disabled={preloading || preloadList.length === 0}
                                        title="Load all configured models into Ollama memory now"
                                    >
                                        <Zap size={14} /> {preloading ? 'Loading...' : 'Preload Now'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* DATA TAB */}
                {activeTab === 'data' && (
                    <div className="max-w-2xl mx-auto">
                        <div className="admin-card">
                            <div className="card-title">
                                <Database size={20} className="text-accent-secondary" />
                                <span>Database Export</span>
                            </div>
                            <p className="card-desc">
                                Download a full JSON dump of the database, including all users, tasks, messages, and configurations.
                                Sensitive data like password hashes are excluded.
                            </p>
                            <button onClick={handleExport} className="btn-primary">
                                <Download size={16} /> Export JSON
                            </button>
                        </div>
                    </div>
                )}

                {/* SECURITY TAB */}
                {
                    activeTab === 'security' && (
                        <div className="max-w-md mx-auto">
                            <div className="admin-card">
                                <div className="card-title mb-6">
                                    <Key size={20} className="text-accent-primary" />
                                    <span>Change My Password</span>
                                </div>

                                <form onSubmit={handleChangePassword}>
                                    <div className="form-group">
                                        <label className="form-label">Current Password</label>
                                        <input
                                            type="password"
                                            className="form-input"
                                            value={oldPassword}
                                            onChange={e => setOldPassword(e.target.value)}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">New Password</label>
                                        <input
                                            type="password"
                                            className="form-input"
                                            value={newPassword}
                                            onChange={e => setNewPassword(e.target.value)}
                                            required
                                        />
                                    </div>

                                    {pwMsg && (
                                        <div className="mb-4 p-3 bg-green-500/10 border border-green-500/20 text-green-400 rounded-lg text-sm flex items-center gap-2">
                                            <Check size={14} /> {pwMsg}
                                        </div>
                                    )}

                                    {pwError && (
                                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm">
                                            {pwError}
                                        </div>
                                    )}

                                    <div className="flex justify-end">
                                        <button type="submit" className="btn-primary">
                                            Update Password
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    )
                }

                {/* LOGS TAB */}
                {activeTab === 'logs' && (
                    <div className="logs-container">
                        <div className="logs-header">
                            <span className="logs-header-title">backend/logs/app.log</span>
                            <button onClick={loadLogs} className="btn-secondary">
                                <RefreshCw size={14} /> Refresh
                            </button>
                        </div>
                        <div className="logs-content">
                            {logs && logs.length > 0 ? logs.join("") : (
                                <div className="logs-empty">No logs found or empty.</div>
                            )}
                        </div>
                    </div>
                )}

                {/* TOOLS TAB */}
                {activeTab === 'tools' && (
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold text-white">MCP Tools</h2>
                            <div className="flex gap-2">
                                <button onClick={loadMcpTools} className="btn-secondary" disabled={mcpToolsLoading}>
                                    <RefreshCw size={14} className={mcpToolsLoading ? 'animate-spin' : ''} /> Refresh List
                                </button>
                                <button onClick={handleRefreshTools} className="btn-secondary" disabled={mcpToolsLoading}>
                                    <Search size={14} /> Re-scan Disk
                                </button>
                            </div>
                        </div>

                        {/* Pending-restart banner — shown when tools were toggled this session */}
                        {pendingRestartTools.size > 0 ? (
                            <div className="tools-restart-warning tools-restart-urgent">
                                <AlertTriangle size={14} />
                                <span>
                                    <strong>{pendingRestartTools.size} tool(s) changed</strong> and need a <strong>Tool Server restart</strong> to take effect.
                                    {' '}Currently-running agents still see the old tool list until restart.
                                    {' '}Changed: {[...pendingRestartTools].join(', ')}
                                </span>
                            </div>
                        ) : (
                            <div className="tools-restart-warning">
                                <AlertTriangle size={14} />
                                <span>Changes to tool enable/disable require <strong>restarting the Tool Server</strong> to take effect. Currently-running agents are unaffected until restart.</span>
                            </div>
                        )}

                        {/* Category filter */}
                        {mcpTools.length > 0 && (
                            <div className="tools-category-filter">
                                {['all', ...new Set(mcpTools.map(t => t.category))].map(cat => (
                                    <button
                                        key={cat}
                                        className={`tools-cat-btn ${mcpToolsCategoryFilter === cat ? 'active' : ''}`}
                                        onClick={() => setMcpToolsCategoryFilter(cat)}
                                    >
                                        {cat}
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Tools table */}
                        <div className="admin-card">
                            {mcpToolsLoading && mcpTools.length === 0 ? (
                                <div className="text-dim text-sm p-4">Loading tools…</div>
                            ) : mcpTools.length === 0 ? (
                                <div className="text-dim text-sm p-4">No tools discovered. Check that the Tool Server is running.</div>
                            ) : (
                                <table className="tools-table">
                                    <thead>
                                        <tr>
                                            <th>Tool</th>
                                            <th>Category</th>
                                            <th>Description</th>
                                            <th>Agent Role</th>
                                            <th className="text-center">LLM</th>
                                            <th className="text-center">Enabled</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {mcpTools
                                            .filter(t => mcpToolsCategoryFilter === 'all' || t.category === mcpToolsCategoryFilter)
                                            .map((tool) => (
                                                <tr key={tool.name} className={`${tool.enabled ? '' : 'tools-row-disabled'} ${pendingRestartTools.has(tool.name) ? 'tools-row-pending' : ''}`}>
                                                    <td className="tools-name-cell font-mono text-xs">
                                                        {tool.name}
                                                        {pendingRestartTools.has(tool.name) && (
                                                            <span className="tools-pending-badge" title="Restart required">⚠ restart</span>
                                                        )}
                                                    </td>
                                                    <td>
                                                        <span className="tools-category-badge">{tool.category}</span>
                                                    </td>
                                                    <td className="tools-desc-cell text-dim">{tool.description}</td>
                                                    <td className="text-xs text-dim">{tool.agent_role || '—'}</td>
                                                    <td className="text-center">
                                                        {tool.is_llm_based && (
                                                            <span className="tools-llm-badge">LLM</span>
                                                        )}
                                                    </td>
                                                    <td className="text-center">
                                                        <button
                                                            className="tools-toggle-btn"
                                                            onClick={() => handleToggleTool(tool.name, tool.enabled)}
                                                            disabled={togglingTool === tool.name}
                                                            title={tool.enabled
                                                                ? 'Click to disable (requires Tool Server restart to take effect)'
                                                                : 'Click to enable (requires Tool Server restart to take effect)'}
                                                        >
                                                            {tool.enabled
                                                                ? <ToggleRight size={20} className="text-green-400" />
                                                                : <ToggleLeft size={20} className="text-dim" />
                                                            }
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        }
                                    </tbody>
                                </table>
                            )}
                        </div>

                        <div className="text-dim text-xs">
                            {mcpTools.filter(t => !t.enabled).length > 0 && (
                                <span>{mcpTools.filter(t => !t.enabled).length} tool(s) disabled. Restart the Tool Server to apply changes.</span>
                            )}
                        </div>
                    </div>
                )}

                {/* TELEMETRY TAB */}
                {activeTab === 'telemetry' && (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold text-white">Usage Telemetry</h2>
                            <button onClick={loadTelemetry} className="btn-secondary" disabled={telemetryLoading}>
                                <RefreshCw size={14} className={telemetryLoading ? 'animate-spin' : ''} /> Refresh
                            </button>
                        </div>

                        {telemetryLoading && !telemetrySummary && (
                            <div className="text-dim text-sm">Loading telemetry…</div>
                        )}

                        {telemetrySummary && (
                            <>
                                {/* Summary Cards */}
                                <div className="telemetry-summary-grid">
                                    <div className="admin-card telemetry-stat-card">
                                        <div className="telemetry-stat-value">{telemetrySummary.total_tasks.toLocaleString()}</div>
                                        <div className="telemetry-stat-label">Total Turns</div>
                                    </div>
                                    <div className="admin-card telemetry-stat-card">
                                        <div className="telemetry-stat-value">{(telemetrySummary.total_tokens / 1000).toFixed(1)}K</div>
                                        <div className="telemetry-stat-label">Total Tokens</div>
                                    </div>
                                    <div className="admin-card telemetry-stat-card">
                                        <div className="telemetry-stat-value">{(telemetrySummary.avg_tokens_per_task / 1000).toFixed(1)}K</div>
                                        <div className="telemetry-stat-label">Avg Tokens / Turn</div>
                                    </div>
                                    <div className="admin-card telemetry-stat-card">
                                        <div className="telemetry-stat-value">{telemetrySummary.active_users}</div>
                                        <div className="telemetry-stat-label">Active Users</div>
                                    </div>
                                    <div className="admin-card telemetry-stat-card">
                                        <div className={`telemetry-stat-value ${telemetrySummary.error_rate > 10 ? 'text-red-400' : ''}`}>
                                            {telemetrySummary.error_rate}%
                                        </div>
                                        <div className="telemetry-stat-label">Error Rate</div>
                                    </div>
                                </div>

                                {/* Timeline Chart */}
                                {telemetryTimeline.length > 0 && (
                                    <div className="admin-card">
                                        <h3 className="text-sm font-semibold text-white mb-4">Tasks per Day (last 30 days)</h3>
                                        <div className="telemetry-timeline-chart">
                                            {(() => {
                                                const maxTasks = Math.max(...telemetryTimeline.map(d => d.tasks), 1);
                                                return telemetryTimeline.map((day, i) => (
                                                    <div key={i} className="telemetry-bar-col" title={`${day.date}: ${day.tasks} turns, ${(day.tokens/1000).toFixed(1)}K tokens`}>
                                                        <div
                                                            className="telemetry-bar"
                                                            style={{ height: `${Math.max(4, (day.tasks / maxTasks) * 100)}%` }}
                                                        />
                                                        {(i === 0 || i === telemetryTimeline.length - 1 || i % 7 === 0) && (
                                                            <span className="telemetry-bar-label">{day.date.slice(5)}</span>
                                                        )}
                                                    </div>
                                                ));
                                            })()}
                                        </div>
                                    </div>
                                )}

                                {/* Models + Tools tables side by side */}
                                <div className="telemetry-tables-grid">
                                    {/* Top Models */}
                                    <div className="admin-card">
                                        <h3 className="text-sm font-semibold text-white mb-3">Top Models</h3>
                                        {telemetrySummary.top_models.length === 0 ? (
                                            <div className="text-dim text-sm">No data yet.</div>
                                        ) : (
                                            <table className="telemetry-table">
                                                <thead>
                                                    <tr>
                                                        <th>Model</th>
                                                        <th className="text-right">Turns</th>
                                                        <th className="text-right">Tokens</th>
                                                        <th className="text-right">Avg / Turn</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {telemetrySummary.top_models.map((m, i) => (
                                                        <tr key={i}>
                                                            <td className="telemetry-model-name">{m.model_identifier}</td>
                                                            <td className="text-right">{m.task_count}</td>
                                                            <td className="text-right">{(m.total_tokens / 1000).toFixed(1)}K</td>
                                                            <td className="text-right">{(m.avg_tokens / 1000).toFixed(1)}K</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        )}
                                    </div>

                                    {/* Top Tools */}
                                    <div className="admin-card">
                                        <h3 className="text-sm font-semibold text-white mb-3">Top Tools</h3>
                                        {telemetrySummary.top_tools.length === 0 ? (
                                            <div className="text-dim text-sm">No tool data yet. Run some tasks first.</div>
                                        ) : (
                                            <table className="telemetry-table">
                                                <thead>
                                                    <tr>
                                                        <th>Tool</th>
                                                        <th className="text-right">Calls</th>
                                                        <th className="text-right">Turns</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {telemetrySummary.top_tools.map((t, i) => (
                                                        <tr key={i}>
                                                            <td className="font-mono text-xs">{t.tool_name}</td>
                                                            <td className="text-right">{t.call_count}</td>
                                                            <td className="text-right">{t.task_count}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        )}
                                    </div>
                                </div>
                            </>
                        )}

                        {!telemetryLoading && !telemetrySummary && (
                            <div className="admin-card text-center py-12 text-dim">
                                <BarChart3 size={40} className="mx-auto mb-3 opacity-30" />
                                <p>No telemetry data yet. Run a few tasks to see stats here.</p>
                            </div>
                        )}
                    </div>
                )}

                {/* SYSTEM TAB */}
                {activeTab === 'system' && systemStats && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* CPU */}
                        <div className="admin-card text-center py-8">
                            <Cpu size={48} className="mx-auto mb-4 text-accent-primary" />
                            <h3 className="text-lg font-medium text-white mb-2">CPU Usage</h3>
                            <div className="text-4xl font-bold text-white mb-2">{systemStats.cpu_percent}%</div>
                            <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                                <div
                                    className={`h-full ${systemStats.cpu_percent > 80 ? 'bg-red-500' : 'bg-green-500'}`}
                                    style={{ width: `${systemStats.cpu_percent}%` }}
                                />
                            </div>
                        </div>

                        {/* RAM */}
                        <div className="admin-card text-center py-8">
                            <Activity size={48} className="mx-auto mb-4 text-purple-400" />
                            <h3 className="text-lg font-medium text-white mb-2">Memory</h3>
                            <div className="text-4xl font-bold text-white mb-2">{systemStats.memory.percent}%</div>
                            <div className="text-xs text-dim mb-2">
                                {(systemStats.memory.available / 1024 / 1024 / 1024).toFixed(1)} GB Available
                            </div>
                            <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                                <div
                                    className={`h-full ${systemStats.memory.percent > 80 ? 'bg-red-500' : 'bg-purple-500'}`}
                                    style={{ width: `${systemStats.memory.percent}%` }}
                                />
                            </div>
                        </div>

                        {/* DISK */}
                        <div className="admin-card text-center py-8">
                            <Database size={48} className="mx-auto mb-4 text-blue-400" />
                            <h3 className="text-lg font-medium text-white mb-2">Disk</h3>
                            <div className="text-4xl font-bold text-white mb-2">{systemStats.disk.percent}%</div>
                            <div className="text-xs text-dim mb-2">
                                {(systemStats.disk.free / 1024 / 1024 / 1024).toFixed(1)} GB Free
                            </div>
                            <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                                <div
                                    className={`h-full ${systemStats.disk.percent > 90 ? 'bg-red-500' : 'bg-blue-500'}`}
                                    style={{ width: `${systemStats.disk.percent}%` }}
                                />
                            </div>
                        </div>
                    </div>
                )}
            </main >

            {/* CREATE USER MODAL */}
            {showCreateModal && (
                <div className="admin-modal-overlay">
                    <div className="admin-modal-content">
                        <button
                            onClick={() => setShowCreateModal(false)}
                            className="admin-modal-close"
                        >
                            <X size={20} />
                        </button>

                        <h3>Create New User</h3>

                        <form onSubmit={handleCreateUser}>
                            <div className="form-group">
                                <label className="form-label">Email</label>
                                <input
                                    type="email"
                                    className="form-input"
                                    value={newUserEmail}
                                    onChange={e => setNewUserEmail(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Password</label>
                                <input
                                    type="password"
                                    className="form-input"
                                    value={newUserPassword}
                                    onChange={e => setNewUserPassword(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Role</label>
                                <select
                                    className="form-input"
                                    value={newUserRole}
                                    onChange={e => setNewUserRole(e.target.value)}
                                >
                                    <option value="user">User</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </div>

                            <div className="admin-modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    Create User
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* EDIT USER MODAL */}
            {showEditModal && editingUser && (
                <div className="admin-modal-overlay">
                    <div className="admin-modal-content">
                        <button
                            onClick={() => { setShowEditModal(false); setEditingUser(null); }}
                            className="admin-modal-close"
                        >
                            <X size={20} />
                        </button>

                        <h3>Edit User</h3>

                        <form onSubmit={handleUpdateUser}>
                            <div className="form-group">
                                <label className="form-label">Email</label>
                                <input
                                    type="email"
                                    className="form-input"
                                    value={editEmail}
                                    onChange={e => setEditEmail(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Password (Reset)</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Leave empty to keep current"
                                    value={editPassword}
                                    onChange={e => setEditPassword(e.target.value)}
                                />
                                <p className="api-key-help-text">Enter a new password to reset it for this user.</p>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Role</label>
                                <select
                                    className="form-input"
                                    value={editRole}
                                    onChange={e => setEditRole(e.target.value)}
                                >
                                    <option value="user">User</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </div>

                            <div className="admin-modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => { setShowEditModal(false); setEditingUser(null); }}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    Update User
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div >
    );
}
