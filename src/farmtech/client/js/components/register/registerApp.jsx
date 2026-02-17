import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { UserPlus, User, Mail, Lock, AlertCircle, CheckCircle } from 'lucide-react';
import api from '../../utils/api';

export const RegisterApp = () => {
    const { t } = useTranslation('register');
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        first_name: '',
        last_name: ''
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (field) => (e) => {
        setFormData(prev => ({ ...prev, [field]: e.target.value }));
        setError('');
    };

    const validateForm = () => {
        if (!formData.username.trim() || !formData.email.trim() || !formData.password.trim()) {
            setError(t('error_required_fields'));
            return false;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email.trim())) {
            setError(t('error_email_invalid'));
            return false;
        }

        if (formData.password !== formData.confirmPassword) {
            setError(t('error_passwords_mismatch'));
            return false;
        }

        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (!validateForm()) return;

        setLoading(true);
        try {
            const payload = {
                username: formData.username.trim(),
                email: formData.email.trim(),
                password: formData.password
            };

            if (formData.first_name.trim()) {
                payload.first_name = formData.first_name.trim();
            }
            if (formData.last_name.trim()) {
                payload.last_name = formData.last_name.trim();
            }

            await api.post('/api/auth/keycloak/register/', payload);

            setSuccess(t('register_success'));
            setFormData({
                username: '',
                email: '',
                password: '',
                confirmPassword: '',
                first_name: '',
                last_name: ''
            });
        } catch (err) {
            if (err.data) {
                if (err.data.username) {
                    setError(t('error_username_taken'));
                } else if (err.data.email) {
                    setError(t('error_email_taken'));
                } else {
                    setError(err.data.detail || err.data.message || t('error_generic'));
                }
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
                            <UserPlus size={48} className="mb-3" />
                            <h1 className="fw-bold mb-2">{t('page_title')}</h1>
                            <p className="lead">{t('page_subtitle')}</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Register Form */}
            <section className="py-5">
                <div className="container">
                    <div className="row justify-content-center">
                        <div className="col-lg-6 col-md-8">
                            <div className="card border-0 shadow-sm">
                                <div className="card-body p-4">
                                    {error && (
                                        <div className="alert alert-danger d-flex align-items-center" role="alert">
                                            <AlertCircle size={20} className="me-2 flex-shrink-0" />
                                            <span>{error}</span>
                                        </div>
                                    )}

                                    {success && (
                                        <div className="alert alert-success d-flex align-items-center" role="alert">
                                            <CheckCircle size={20} className="me-2 flex-shrink-0" />
                                            <span>{success}</span>
                                        </div>
                                    )}

                                    <form onSubmit={handleSubmit}>
                                        <div className="mb-3">
                                            <label htmlFor="username" className="form-label fw-semibold">
                                                <User size={16} className="me-1" />
                                                {t('username_label')} *
                                            </label>
                                            <input
                                                type="text"
                                                className="form-control"
                                                id="username"
                                                placeholder={t('username_placeholder')}
                                                value={formData.username}
                                                onChange={handleChange('username')}
                                                disabled={loading}
                                                autoFocus
                                            />
                                        </div>

                                        <div className="mb-3">
                                            <label htmlFor="email" className="form-label fw-semibold">
                                                <Mail size={16} className="me-1" />
                                                {t('email_label')} *
                                            </label>
                                            <input
                                                type="email"
                                                className="form-control"
                                                id="email"
                                                placeholder={t('email_placeholder')}
                                                value={formData.email}
                                                onChange={handleChange('email')}
                                                disabled={loading}
                                            />
                                        </div>

                                        <div className="mb-3">
                                            <label htmlFor="password" className="form-label fw-semibold">
                                                <Lock size={16} className="me-1" />
                                                {t('password_label')} *
                                            </label>
                                            <input
                                                type="password"
                                                className="form-control"
                                                id="password"
                                                placeholder={t('password_placeholder')}
                                                value={formData.password}
                                                onChange={handleChange('password')}
                                                disabled={loading}
                                            />
                                        </div>

                                        <div className="mb-3">
                                            <label htmlFor="confirmPassword" className="form-label fw-semibold">
                                                <Lock size={16} className="me-1" />
                                                {t('confirm_password_label')} *
                                            </label>
                                            <input
                                                type="password"
                                                className="form-control"
                                                id="confirmPassword"
                                                placeholder={t('confirm_password_placeholder')}
                                                value={formData.confirmPassword}
                                                onChange={handleChange('confirmPassword')}
                                                disabled={loading}
                                            />
                                        </div>

                                        <div className="row">
                                            <div className="col-md-6 mb-3">
                                                <label htmlFor="firstName" className="form-label fw-semibold">
                                                    {t('first_name_label')}
                                                    <span className="text-muted fw-normal ms-1">({t('optional')})</span>
                                                </label>
                                                <input
                                                    type="text"
                                                    className="form-control"
                                                    id="firstName"
                                                    placeholder={t('first_name_placeholder')}
                                                    value={formData.first_name}
                                                    onChange={handleChange('first_name')}
                                                    disabled={loading}
                                                />
                                            </div>
                                            <div className="col-md-6 mb-3">
                                                <label htmlFor="lastName" className="form-label fw-semibold">
                                                    {t('last_name_label')}
                                                    <span className="text-muted fw-normal ms-1">({t('optional')})</span>
                                                </label>
                                                <input
                                                    type="text"
                                                    className="form-control"
                                                    id="lastName"
                                                    placeholder={t('last_name_placeholder')}
                                                    value={formData.last_name}
                                                    onChange={handleChange('last_name')}
                                                    disabled={loading}
                                                />
                                            </div>
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
                                        <span className="text-muted">{t('has_account')} </span>
                                        <a href="/account/login/" className="fw-semibold text-decoration-none"
                                           style={{ color: 'var(--gn-primary, #397aab)' }}>
                                            {t('login_link')}
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
