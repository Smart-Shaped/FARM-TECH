import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { LogIn, User, Lock, AlertCircle } from 'lucide-react';
import api from '../../utils/api';

export const LoginApp = () => {
    const { t } = useTranslation('login');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!username.trim() || !password.trim()) {
            setError(t('error_required_fields'));
            return;
        }

        setLoading(true);
        try {
            const data = await api.post('/api/auth/keycloak/', {
                username: username.trim(),
                password
            });

            if (data.token) {
                window.location.href = '/';
            }
        } catch (err) {
            if (err.status === 401 || err.status === 400) {
                setError(t('error_invalid_credentials'));
            } else {
                setError(t('error_generic'));
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="gn-theme gn-homepage">
            {/* Hero Section */}
            <section className="hero-gradient text-white py-5">
                <div className="container">
                    <div className="row justify-content-center">
                        <div className="col-lg-6 text-center">
                            <LogIn size={48} className="mb-3" />
                            <h1 className="fw-bold mb-2">{t('page_title')}</h1>
                            <p className="lead">{t('page_subtitle')}</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Login Form */}
            <section className="py-5">
                <div className="container">
                    <div className="row justify-content-center">
                        <div className="col-lg-5 col-md-7">
                            <div className="card border-0 shadow-sm">
                                <div className="card-body p-4">
                                    {error && (
                                        <div className="alert alert-danger d-flex align-items-center" role="alert">
                                            <AlertCircle size={20} className="me-2 flex-shrink-0" />
                                            <span>{error}</span>
                                        </div>
                                    )}

                                    <form onSubmit={handleSubmit}>
                                        <div className="mb-3">
                                            <label htmlFor="username" className="form-label fw-semibold">
                                                <User size={16} className="me-1" />
                                                {t('username_label')}
                                            </label>
                                            <input
                                                type="text"
                                                className="form-control"
                                                id="username"
                                                placeholder={t('username_placeholder')}
                                                value={username}
                                                onChange={(e) => setUsername(e.target.value)}
                                                disabled={loading}
                                                autoFocus
                                            />
                                        </div>

                                        <div className="mb-4">
                                            <label htmlFor="password" className="form-label fw-semibold">
                                                <Lock size={16} className="me-1" />
                                                {t('password_label')}
                                            </label>
                                            <input
                                                type="password"
                                                className="form-control"
                                                id="password"
                                                placeholder={t('password_placeholder')}
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                disabled={loading}
                                            />
                                        </div>

                                        <button
                                            type="submit"
                                            className="btn btn-primary w-100 py-2 fw-semibold"
                                            disabled={loading}
                                            style={{
                                                background: 'linear-gradient(135deg, var(--gn-primary-dark, #2e5f7d) 0%, var(--gn-primary, #397aab) 100%)',
                                                borderColor: 'var(--gn-primary, #397aab)'
                                            }}
                                        >
                                            {loading ? t('loading_button') : t('submit_button')}
                                        </button>
                                    </form>

                                    <div className="text-center mt-3">
                                        <span className="text-muted">{t('no_account')} </span>
                                        <a href="/account/signup/" className="fw-semibold text-decoration-none"
                                           style={{ color: 'var(--gn-primary, #397aab)' }}>
                                            {t('register_link')}
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
};
