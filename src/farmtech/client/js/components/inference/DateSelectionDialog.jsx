import React, { useState } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const DateSelectionDialog = ({ onClose, onConfirm, initialStartDate = '', initialEndDate = '' }) => {
    const { t } = useTranslation('inference');
    const [startDate, setStartDate] = useState(initialStartDate);
    const [endDate, setEndDate] = useState(initialEndDate);
    const [error, setError] = useState('');

    const handleConfirm = () => {
        if (!startDate || !endDate) {
            setError(t('date_required', 'Both dates are required'));
            return;
        }

        if (new Date(startDate) > new Date(endDate)) {
            setError(t('invalid_date_range', 'Start date must be before end date'));
            return;
        }

        onConfirm(startDate, endDate);
    };

    const showWarning = startDate && endDate;

    return (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
            <div className="modal-dialog modal-dialog-centered">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">
                            {t('select_date_range', 'Select Date Range for Analysis')}
                        </h5>
                        <button
                            type="button"
                            className="btn-close"
                            onClick={onClose}
                            aria-label="Close"
                        ></button>
                    </div>
                    <div className="modal-body">
                        <div className="mb-3">
                            <label htmlFor="start-date" className="form-label">
                                {t('start_date', 'Start Date')}
                            </label>
                            <input
                                type="date"
                                className="form-control"
                                id="start-date"
                                value={startDate}
                                onChange={(e) => {
                                    setStartDate(e.target.value);
                                    setError('');
                                }}
                                required
                            />
                        </div>

                        <div className="mb-3">
                            <label htmlFor="end-date" className="form-label">
                                {t('end_date', 'End Date')}
                            </label>
                            <input
                                type="date"
                                className="form-control"
                                id="end-date"
                                value={endDate}
                                onChange={(e) => {
                                    setEndDate(e.target.value);
                                    setError('');
                                }}
                                required
                            />
                        </div>

                        {error && (
                            <div className="alert alert-danger d-flex align-items-center">
                                <X size={20} className="me-2" />
                                {error}
                            </div>
                        )}

                        {showWarning && !error && (
                            <div className="alert alert-warning d-flex align-items-start">
                                <AlertTriangle size={20} className="me-2 mt-1 flex-shrink-0" />
                                <div>
                                    <strong>{t('warning', 'Warning:')}</strong>{' '}
                                    {t('cloud_warning', 'If cloud coverage exceeds 20% or there are satellite passage issues in the selected date range, we recommend using a date range at least 70 days before the estimated harvest.')}
                                </div>
                            </div>
                        )}
                    </div>
                    <div className="modal-footer">
                        <button
                            type="button"
                            className="btn btn-secondary text-white"
                            onClick={onClose}
                        >
                            {t('cancel', 'Cancel')}
                        </button>
                        <button
                            type="button"
                            className="btn btn-primary"
                            onClick={handleConfirm}
                            disabled={!startDate || !endDate}
                        >
                            {t('confirm_analysis', 'Confirm Analysis')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

