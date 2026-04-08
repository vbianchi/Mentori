import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import config from '../../config';
import './LoginPage.css';

export default function LoginPage() {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const formData = new URLSearchParams();
            formData.append('username', email); // OAuth2 expects 'username'
            formData.append('password', password);

            const res = await fetch(`${config.API_BASE_URL}/auth/token`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Login failed");
            }

            const data = await res.json();
            localStorage.setItem("mentori_token", data.access_token);
            navigate("/");
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            {/* Background Effects */}
            <div className="login-bg-glow glow-1" />
            <div className="login-bg-glow glow-2" />

            <div className="login-card">
                <div className="login-header">
                    <h1 className="login-title">Mentor<span className="login-accent">::</span>i</h1>
                    <p className="login-subtitle">Sign in to your research workspace</p>
                    <div className="login-status">
                        <div className="login-status-dot"></div>
                        <span>System Online</span>
                    </div>
                </div>

                <form onSubmit={handleLogin} className="login-form">
                    <div className="input-group">
                        <label className="input-label">Email</label>
                        <div className="input-wrapper">
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="login-input"
                                placeholder="name@example.com"
                                required
                            />
                            <User className="input-icon" size={16} />
                        </div>
                    </div>

                    <div className="input-group">
                        <label className="input-label">Password</label>
                        <div className="input-wrapper">
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="login-input"
                                placeholder="••••••••"
                                required
                            />
                            <Lock className="input-icon" size={16} />
                        </div>
                    </div>

                    {error && (
                        <div className="error-banner">
                            <AlertCircle size={14} />
                            <span>{error}</span>
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="login-btn"
                    >
                        {loading ? (
                            <Loader2 size={18} className="animate-spin" />
                        ) : (
                            <>
                                <span>Sign In</span>
                                <ArrowRight size={16} />
                            </>
                        )}
                    </button>
                </form>

                <div className="login-footer">
                    <p>Protected System · Authorized Access Only</p>
                    <p className="login-version">v2.3 · Build 2026.01</p>
                </div>
            </div>
        </div>
    );
}
