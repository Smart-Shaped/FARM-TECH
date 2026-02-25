import { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
export const PermissionRequestDialog = ({ onClose }) => {
    const { t } = useTranslation('permission');
    const [researchLines, setResearchLines] = useState([]);
    const [selectedLine, setSelectedLine] = useState('');
    const [requestedRole, setRequestedRole] = useState('');
    const [motivation, setMotivation] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ text: '', type: '' });
    const [submitting, setSubmitting] = useState(false);

    // Load research lines on mount
    useEffect(() => {
        loadResearchLines();
    }, []);

    const loadResearchLines = async () => {
        setLoading(true);
        try {
            const data = await api.get('/api/group/list/');
            setResearchLines(data.groups || []);
        } catch (error) {
            console.error('Error loading research lines:', error);
            setMessage({
                text: t('error_loading_lines', 'Error loading research lines'),
                type: 'danger',
            });
        } finally {
            setLoading(false);
        }
    };

    const getSelectedLineData = () => {
        return researchLines.find((line) => String(line.id) === selectedLine);
    };

    const canSubmit = () => {
        // L'utente può fare submit solo se ha compilato tutti i campi
        // Il controllo del permesso farmtech.can_request_permissions è già fatto nel template Django
        return selectedLine && requestedRole && motivation.trim();
    };

    const handleSubmit = async () => {
        if (!canSubmit()) return;

        setSubmitting(true);
        setMessage({ text: t('submitting', 'Submitting...'), type: 'info' });

        try {
            // Get the selected research line data to get the name
            const lineData = getSelectedLineData();

            await api.post('/api/group/group-join-request/', {
                group_profile_id: lineData.id,
                requested_role: requestedRole,
                motivation: motivation.trim(),
            });

            setMessage({
                text: t('request_sent', 'Request sent successfully!'),
                type: 'success',
            });

            setTimeout(() => {
                onClose();
            }, 2000);
        } catch (error) {
            console.error('Error submitting request:', error);
            setMessage({
                text: error.message || t('error_submitting', 'Error submitting request. Please try again.'),
                type: 'danger',
            });
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div
            className="modal show d-block"
            tabIndex="-1"
            style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
            onClick={(e) => {
                if (e.target.classList.contains('modal')) {
                    onClose();
                }
            }}
        >
            <div className="modal-dialog modal-dialog-centered">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">{t('request_permissions', 'Request Permissions')}</h5>
                        <button
                            type="button"
                            className="btn-close"
                            onClick={onClose}
                            aria-label="Close"
                        ></button>
                    </div>

                    <div className="modal-body">
                        <p className="text-muted mb-4">
                            {t(
                                'request_description',
                                'Submit a request to obtain uploader or manager permissions for a specific research line.'
                            )}
                        </p>

                        {/* Research Line Select */}
                        <div className="mb-3">
                            <label htmlFor="research-line" className="form-label">
                                {t('research_line', 'Research Line')}
                            </label>
                            <select
                                id="research-line"
                                className="form-select"
                                value={selectedLine}
                                onChange={(e) => {
                                    setSelectedLine(e.target.value);
                                    setMessage({ text: '', type: '' });
                                }}
                                disabled={loading}
                            >
                                <option value="">
                                    {loading
                                        ? t('loading', 'Loading...')
                                        : t('select_line', 'Select a research line')}
                                </option>
                                {researchLines.map((line) => (
                                    <option key={line.id} value={line.id}>
                                        {line.title}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Requested Role Select */}
                        <div className="mb-3">
                            <label htmlFor="requested-role" className="form-label">
                                {t('requested_role', 'Requested Role')}
                            </label>
                            <select
                                id="requested-role"
                                className="form-select"
                                value={requestedRole}
                                onChange={(e) => {
                                    setRequestedRole(e.target.value);
                                    setMessage({ text: '', type: '' });
                                }}
                                disabled={!selectedLine}
                            >
                                <option value="">{t('select_role', 'Select a role')}</option>
                                <option value="member">Uploader</option>
                                <option value="manager">Manager</option>
                            </select>
                        </div>

                        {/* Motivation Textarea */}
                        <div className="mb-3">
                            <label htmlFor="motivation" className="form-label">
                                {t('motivation', 'Motivation')}
                            </label>
                            <textarea
                                id="motivation"
                                className="form-control"
                                rows="4"
                                value={motivation}
                                onChange={(e) => {
                                    setMotivation(e.target.value);
                                    setMessage({ text: '', type: '' });
                                }}
                                placeholder={t(
                                    'motivation_placeholder',
                                    'Explain why you need this permission...'
                                )}
                                disabled={!requestedRole}
                            />
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
                            {t('cancel', 'Cancel')}
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
                                    {t('submitting', 'Submitting...')}
                                </>
                            ) : (
                                t('submit_request', 'Submit Request')
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};