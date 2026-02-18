import { useState } from 'react';
import { AlertCircle, CheckCircle, Loader, Eye, EyeOff } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';

export const ChangePasswordDialog = ({ onClose }) => {
    const { t } = useTranslation('changePassword');
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showOld, setShowOld] = useState(false);
    const [showNew, setShowNew] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState({ text: '', type: '' });

    const canSubmit = () => {
        return oldPassword && newPassword && confirmPassword && newPassword === confirmPassword;
    };

    const handleSubmit = async () => {
        if (!canSubmit()) return;

        if (newPassword !== confirmPassword) {
            setMessage({ text: t('passwords_mismatch'), type: 'danger' });
            return;
        }

        setSubmitting(true);
        setMessage({ text: t('submitting'), type: 'info' });

        try {
            await api.post('/api/auth/change-password/', {
                old_password: oldPassword,
                new_password: newPassword,
                new_password_confirm: confirmPassword,
            });

            setMessage({ text: t('password_changed'), type: 'success' });
            setTimeout(() => {                
                window.location.href = '/account/login';
            }, 2000);
        } catch (error) {
            const errorData = error.data;
            let errorMsg = t('error_generic');

            if (errorData) {
                if (errorData.old_password) {
                    errorMsg = t('error_old_password');
                } else if (errorData.new_password) {
                    errorMsg = Array.isArray(errorData.new_password)
                        ? errorData.new_password.join(' ')
                        : errorData.new_password;
                } else if (errorData.detail) {
                    errorMsg = errorData.detail;
                }
            }

            setMessage({ text: errorMsg, type: 'danger' });
        } finally {
            setSubmitting(false);
        }
    };

    const passwordsMatch = !confirmPassword || newPassword === confirmPassword;

    return (
        <div
            className="modal show d-block"
            tabIndex="-1"
            style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
            onClick={(e) => {
                if (e.target.classList.contains('modal')) onClose();
            }}
        >
            <div className="modal-dialog modal-dialog-centered">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">{t('change_password')}</h5>
                        <button
                            type="button"
                            className="btn-close"
                            onClick={onClose}
                            aria-label="Close"
                        ></button>
                    </div>

                    <div className="modal-body">
                        {/* Old Password */}
                        <div className="mb-3">
                            <label htmlFor="old-password" className="form-label">
                                {t('old_password')}
                            </label>
                            <div className="input-group">
                                <input
                                    id="old-password"
                                    type={showOld ? 'text' : 'password'}
                                    className="form-control"
                                    value={oldPassword}
                                    onChange={(e) => {
                                        setOldPassword(e.target.value);
                                        setMessage({ text: '', type: '' });
                                    }}
                                    disabled={submitting}
                                />
                                <button
                                    type="button"
                                    className="btn btn-outline-secondary"
                                    onClick={() => setShowOld(!showOld)}
                                    tabIndex={-1}
                                >
                                    {showOld ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                        </div>

                        {/* New Password */}
                        <div className="mb-3">
                            <label htmlFor="new-password" className="form-label">
                                {t('new_password')}
                            </label>
                            <div className="input-group">
                                <input
                                    id="new-password"
                                    type={showNew ? 'text' : 'password'}
                                    className="form-control"
                                    value={newPassword}
                                    onChange={(e) => {
                                        setNewPassword(e.target.value);
                                        setMessage({ text: '', type: '' });
                                    }}
                                    disabled={submitting}
                                />
                                <button
                                    type="button"
                                    className="btn btn-outline-secondary"
                                    onClick={() => setShowNew(!showNew)}
                                    tabIndex={-1}
                                >
                                    {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                        </div>

                        {/* Confirm New Password */}
                        <div className="mb-3">
                            <label htmlFor="confirm-password" className="form-label">
                                {t('confirm_password')}
                            </label>
                            <div className="input-group">
                                <input
                                    id="confirm-password"
                                    type={showConfirm ? 'text' : 'password'}
                                    className={`form-control ${!passwordsMatch ? 'is-invalid' : ''}`}
                                    value={confirmPassword}
                                    onChange={(e) => {
                                        setConfirmPassword(e.target.value);
                                        setMessage({ text: '', type: '' });
                                    }}
                                    disabled={submitting}
                                />
                                <button
                                    type="button"
                                    className="btn btn-outline-secondary"
                                    onClick={() => setShowConfirm(!showConfirm)}
                                    tabIndex={-1}
                                >
                                    {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                            {!passwordsMatch && (
                                <div className="invalid-feedback d-block">
                                    {t('passwords_mismatch')}
                                </div>
                            )}
                        </div>

                        {/* Message Display */}
                        {message.text && (
                            <div className={`alert alert-${message.type} d-flex align-items-center`}>
                                {message.type === 'success' && (
                                    <CheckCircle size={20} className="me-2 flex-shrink-0" />
                                )}
                                {message.type === 'danger' && (
                                    <AlertCircle size={20} className="me-2 flex-shrink-0" />
                                )}
                                {message.type === 'info' && (
                                    <Loader size={20} className="me-2 flex-shrink-0 upload-status-loading" />
                                )}
                                <div>{message.text}</div>
                            </div>
                        )}
                    </div>

                    <div className="modal-footer">
                        <button
                            type="button"
                            className="btn btn-secondary text-white"
                            onClick={onClose}
                            disabled={submitting}
                        >
                            {t('cancel')}
                        </button>
                        <button
                            type="button"
                            className="btn btn-primary"
                            onClick={handleSubmit}
                            disabled={!canSubmit() || submitting}
                        >
                            {submitting ? (
                                <>
                                    <Loader size={16} className="me-2 upload-status-loading" />
                                    {t('submitting')}
                                </>
                            ) : (
                                t('submit')
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
