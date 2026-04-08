import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, Key, Bot, Settings as SettingsIcon, AlertCircle, ChevronLeft, Database, User } from 'lucide-react';
import config from '../../config';
import '../admin/AdminDashboard.css'; // Reuse Admin styles for consistency
import './SettingsPage.css';
import CollectionSettingsTab from './CollectionSettingsTab';

export default function SettingsPage() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('agents');
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState(null);
    const [error, setError] = useState(null);

    // State
    const [availableModels, setAvailableModels] = useState([]);
    const [userId, setUserId] = useState(null);
    const [settings, setSettings] = useState({
        agent_roles: {
            lead_researcher: "",
            supervisor: "",
            librarian: "",
            coder: "",
            handyman: "",
            editor: "",
            transcriber: "",
            vision: "",
            default: ""
        },
        api_keys: {
            GEMINI_API_KEY: "",
            TAVILY_API_KEY: ""
        },
        profile_image: "",
        first_name: "",
        last_name: "",
        preferences: "",
        require_plan_approval: false
    });

    // Generate expanded model options including thinking variants
    const getExpandedModelOptions = () => {
        const options = [];
        for (const model of availableModels) {
            // Always add the base model (no thinking)
            options.push({
                value: model.model_identifier,
                label: `${model.model_identifier.split('::')[1]} (${model.provider})`,
                isThinking: false
            });

            // Add thinking variants if model supports thinking
            if (model.supports_thinking) {
                if (model.thinking_type === 'level') {
                    // GPT-OSS style: add low/medium/high variants
                    options.push({
                        value: `${model.model_identifier}[think:low]`,
                        label: `${model.model_identifier.split('::')[1]} (${model.provider}) [think low]`,
                        isThinking: true,
                        thinkLevel: 'low'
                    });
                    options.push({
                        value: `${model.model_identifier}[think:medium]`,
                        label: `${model.model_identifier.split('::')[1]} (${model.provider}) [think medium]`,
                        isThinking: true,
                        thinkLevel: 'medium'
                    });
                    options.push({
                        value: `${model.model_identifier}[think:high]`,
                        label: `${model.model_identifier.split('::')[1]} (${model.provider}) [think high]`,
                        isThinking: true,
                        thinkLevel: 'high'
                    });
                } else {
                    // Boolean thinking: add single [think] variant
                    options.push({
                        value: `${model.model_identifier}[think]`,
                        label: `${model.model_identifier.split('::')[1]} (${model.provider}) [think]`,
                        isThinking: true
                    });
                }
            }
        }
        return options;
    };

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("mentori_token");

            const modelsRes = await fetch(`${config.API_BASE_URL}/users/models`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (modelsRes.status === 401) {
                navigate('/login');
                return;
            }
            if (!modelsRes.ok) throw new Error("Failed to load models. Ensure backend is running.");
            const modelsData = await modelsRes.json();
            setAvailableModels(modelsData);

            // 2. Fetch User Settings
            const userRes = await fetch(`${config.API_BASE_URL}/users/me`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!userRes.ok) throw new Error("Failed to load user settings");
            const userData = await userRes.json();

            // Merge defaults
            setUserId(userData.id);
            setSettings(prev => ({
                agent_roles: { ...prev.agent_roles, ...(userData.settings?.agent_roles || {}) },
                api_keys: { ...prev.api_keys, ...(userData.settings?.api_keys || {}) },
                profile_image: userData.profile_image || "",
                first_name: userData.first_name || "",
                last_name: userData.last_name || "",
                preferences: userData.preferences || "",
                require_plan_approval: userData.settings?.require_plan_approval || false
            }));

        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setMsg(null);
        setError(null);
        try {
            const token = localStorage.getItem("mentori_token");
            const res = await fetch(`${config.API_BASE_URL}/users/me/settings`, {
                method: "PATCH",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    settings: {
                        agent_roles: settings.agent_roles,
                        api_keys: settings.api_keys,
                        require_plan_approval: settings.require_plan_approval
                    },
                    profile_image: settings.profile_image,
                    first_name: settings.first_name,
                    last_name: settings.last_name,
                    preferences: settings.preferences
                })
            });

            if (!res.ok) throw new Error("Failed to save settings");
            setMsg("Settings saved successfully!");

            // Clear message after 3s
            setTimeout(() => setMsg(null), 3000);
        } catch (e) {
            setError(e.message);
        }
    };

    const updateBinding = (role, modelId) => {
        setSettings(prev => ({
            ...prev,
            agent_roles: {
                ...prev.agent_roles,
                [role]: modelId
            }
        }));
    };

    const updateApiKey = (key, value) => {
        setSettings(prev => ({
            ...prev,
            api_keys: {
                ...prev.api_keys,
                [key]: value
            }
        }));
    };

    // Get expanded options once (memoized by availableModels changes)
    const modelOptions = getExpandedModelOptions();

    return (
        <div className="admin-container"> {/* Reusing Admin Container Class */}

            {/* Header */}
            <header className="admin-header">
                <div className="admin-brand">
                    <SettingsIcon size={24} className="text-accent-primary" />
                    <span>User Settings</span>
                </div>

                <nav className="admin-nav">
                    <button
                        className={`admin-tab ${activeTab === 'agents' ? 'active' : ''}`}
                        onClick={() => setActiveTab('agents')}
                    >
                        <Bot size={16} /> Agent Roles
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'collections' ? 'active' : ''}`}
                        onClick={() => setActiveTab('collections')}
                    >
                        <Database size={16} /> Knowledge Base
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'keys' ? 'active' : ''}`}
                        onClick={() => setActiveTab('keys')}
                    >
                        <Key size={16} /> API Keys
                    </button>
                    <button
                        className={`admin-tab ${activeTab === 'profile' ? 'active' : ''}`}
                        onClick={() => setActiveTab('profile')}
                    >
                        <SettingsIcon size={16} /> Profile
                    </button>
                </nav>

                <div className="admin-actions">
                    <button onClick={() => navigate('/')} className="btn-header">
                        <ChevronLeft size={16} /> Back to App
                    </button>
                    <button onClick={handleSave} className="btn-primary" disabled={loading}>
                        {loading ? 'Saving...' : 'Save Changes'}
                        <Save size={16} />
                    </button>
                </div>
            </header>

            {/* Content */}
            <main className="admin-content animate-fade-in">

                {/* STATUS MESSAGES */}
                {error && (
                    <div className="alert-error">
                        <AlertCircle size={18} /> {error}
                    </div>
                )}
                {msg && (
                    <div className="alert-success">
                        <Save size={18} /> {msg}
                    </div>
                )}

                {/* AGENT BINDINGS TAB */}
                {activeTab === 'agents' && (
                    <div className="settings-content-wrapper">
                        <div className="admin-card">
                            <div className="card-title">
                                <Bot size={20} className="text-accent-secondary" />
                                <span>Team Roles (The Ensemble)</span>
                            </div>
                            <p className="card-desc">
                                Assign specific models to each agent role. The Lead Researcher delegates tasks to these specialized agents.
                                Only models whitelisted by the Admin are shown here.
                            </p>

                            <div className="agent-roles-grid">
                                {[
                                    { role: 'lead_researcher', label: 'Lead Researcher', sub: 'Orchestration & Planning', colorClass: 'lead', hint: 'Use your best reasoning model. This role orchestrates the entire task — quality here directly impacts results.' },
                                    { role: 'supervisor', label: 'Supervisor Agent', sub: 'Quality Evaluation & Retry Logic', colorClass: 'lead', hint: 'Runs after every step. Choose a fast model with strong instruction-following to avoid evaluation bottlenecks.' },
                                    { role: 'librarian', label: 'Librarian Agent', sub: 'Memory Consolidation & Context', colorClass: 'editor', hint: 'A mid-tier model works well here. Responsible for summarizing memory and maintaining task context.' },
                                    { role: 'coder', label: 'Coder Agent', sub: 'Python & Analysis', colorClass: 'coder', hint: 'Use a code-specialized model (e.g. qwen-coder). Avoid think:high — benchmark V2-8 shows it reduces pass rate.' },
                                    { role: 'handyman', label: 'Handyman Agent', sub: 'Tools & Search', colorClass: 'handyman', hint: 'Use a model with good tool-use/function-calling. Executes bash, file, and search tools.' },
                                    { role: 'editor', label: 'Editor Agent', sub: 'Writing & Formatting', colorClass: 'editor', hint: 'A model with strong writing and markdown capabilities. Used for final report generation and formatting.' },
                                    { role: 'transcriber', label: 'Transcriber Agent', sub: 'Vision OCR & Document Analysis', colorClass: 'transcriber', hint: 'Must be a vision-capable model. Used for image and PDF OCR. Leave blank to skip VLM extraction.' },
                                    { role: 'vision', label: 'Vision Agent', sub: 'Image Analysis & Verification', colorClass: 'transcriber', hint: 'Vision-capable model for analyzing charts, figures, and screenshots during task execution.' },
                                    { role: 'default', label: 'Default Agent', sub: 'Fallback for all roles', colorClass: 'default', hint: 'Fallback model used when a role has no specific assignment.' }
                                ].map(({ role, label, sub, colorClass, hint }) => (
                                    <div key={role} className="agent-role-card">
                                        <label className={`agent-role-title ${colorClass}`}>{label}</label>
                                        <p className="agent-role-subtitle">{sub}</p>
                                        <select
                                            value={settings.agent_roles[role]}
                                            onChange={(e) => updateBinding(role, e.target.value)}
                                            className="form-input"
                                        >
                                            <option value="">Select a model...</option>
                                            {modelOptions.map(opt => (
                                                <option
                                                    key={opt.value}
                                                    value={opt.value}
                                                    className={opt.isThinking ? 'thinking-option' : ''}
                                                >
                                                    {opt.label}
                                                </option>
                                            ))}
                                        </select>
                                        <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', marginTop: '6px', lineHeight: '1.4' }}>{hint}</p>
                                        {role === 'coder' && settings.agent_roles.coder?.includes('[think:high]') && (
                                            <div className="alert-warning" style={{ marginTop: '8px', fontSize: '0.8rem' }}>
                                                <AlertCircle size={13} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                                                <strong>think:high not recommended for Coder.</strong> Benchmark V2-8 shows think:high reduces code pass rate from 74% to 6% on this model. Use the base model or think:low instead.
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {availableModels.length === 0 && (
                                <div className="alert-warning">
                                    No models found? Ask your Admin to sync and enable models in the Admin Console.
                                </div>
                            )}
                        </div>

                        {/* COLLABORATION SETTINGS */}
                        <div className="admin-card mt-6">
                            <div className="card-title">
                                <AlertCircle size={20} className="text-accent-secondary" />
                                <span>Collaboration Settings</span>
                            </div>

                            <div className="flex items-center justify-between p-4 bg-[#1e1e1e] rounded-lg border border-white/5">
                                <div>
                                    <h4 className="text-white font-medium mb-1">Require Plan Approval</h4>
                                    <p className="text-sm text-gray-400">
                                        When enabled, the agent will pause after generating an execution plan and wait for your approval before proceeding.
                                    </p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        className="sr-only peer"
                                        checked={settings.require_plan_approval}
                                        onChange={(e) => setSettings({ ...settings, require_plan_approval: e.target.checked })}
                                    />
                                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-secondary"></div>
                                </label>
                            </div>
                        </div>
                    </div>
                )}

                {/* KNOWLEDGE BASE TAB */}
                {activeTab === 'collections' && (
                    <CollectionSettingsTab />
                )}

                {/* API KEYS TAB */}
                {activeTab === 'keys' && (
                    <div className="settings-content-narrow">
                        <div className="admin-card">
                            <div className="card-title">
                                <Key size={20} className="text-accent-primary" />
                                <span>External Service Keys</span>
                            </div>

                            <div className="api-keys-container">
                                <div className="form-group">
                                    <label className="form-label">Gemini API Key</label>
                                    <input
                                        type="password"
                                        className="form-input"
                                        placeholder="AIzaSy..."
                                        value={settings.api_keys.GEMINI_API_KEY}
                                        onChange={(e) => updateApiKey('GEMINI_API_KEY', e.target.value)}
                                    />
                                    <p className="api-key-help-text">Required for Google Gemini models.</p>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Tavily API Key</label>
                                    <input
                                        type="password"
                                        className="form-input"
                                        placeholder="tvly-..."
                                        value={settings.api_keys.TAVILY_API_KEY}
                                        onChange={(e) => updateApiKey('TAVILY_API_KEY', e.target.value)}
                                    />
                                    <p className="api-key-help-text">Required for Web Search & Research tools.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* PROFILE TAB */}
                {activeTab === 'profile' && (
                    <div className="settings-content-narrow">
                        <div className="admin-card">
                            <div className="card-title">
                                <User size={20} className="text-accent-primary" />
                                <span>User Profile</span>
                            </div>

                            {/* Name Fields */}
                            <div className="profile-name-row">
                                <div className="form-group">
                                    <label className="form-label">First Name</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="John"
                                        value={settings.first_name}
                                        onChange={(e) => setSettings({ ...settings, first_name: e.target.value })}
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Last Name</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="Doe"
                                        value={settings.last_name}
                                        onChange={(e) => setSettings({ ...settings, last_name: e.target.value })}
                                    />
                                </div>
                            </div>

                            {/* Profile Image */}
                            <div className="profile-info-card">
                                <label className="profile-label">Profile Image URL</label>
                                <div className="flex gap-4 items-center">
                                    <input
                                        type="text"
                                        className="form-input flex-1"
                                        placeholder="https://example.com/avatar.png"
                                        value={settings.profile_image}
                                        onChange={(e) => setSettings({ ...settings, profile_image: e.target.value })}
                                    />
                                    {settings.profile_image && (
                                        <div className="w-10 h-10 rounded-full overflow-hidden border border-white/20">
                                            <img src={settings.profile_image} alt="Avatar Preview" className="w-full h-full object-cover" />
                                        </div>
                                    )}
                                </div>
                                <p className="profile-help-text">
                                    Enter a public URL for your profile picture.
                                </p>
                            </div>

                            {/* Preferences */}
                            <div className="profile-info-card mt-4">
                                <label className="profile-label">Preferences & Context</label>
                                <textarea
                                    className="form-input form-textarea"
                                    placeholder="Tell the AI about yourself, your preferences, expertise level, communication style, etc. This context will be shared with the AI to personalize responses."
                                    value={settings.preferences}
                                    onChange={(e) => setSettings({ ...settings, preferences: e.target.value })}
                                    rows={5}
                                />
                                <p className="profile-help-text">
                                    This information will be injected into the LLM context to personalize AI responses.
                                    For example: "I'm a senior developer who prefers concise explanations with code examples."
                                </p>
                            </div>

                            {/* User ID */}
                            <div className="profile-info-card mt-4">
                                <label className="profile-label">User ID (UUID)</label>
                                <div className="profile-value">
                                    {userId || "Loading..."}
                                </div>
                                <p className="profile-help-text">
                                    This is your unique workspace identifier. Folders are located at <code>workspace/&#123;uuid&#125;</code>.
                                </p>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
