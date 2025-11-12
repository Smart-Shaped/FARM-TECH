import { Info, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const TiffInfoDialog = ({ onClose, onConfirm }) => {
    const { t } = useTranslation('inference');

    return (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
            <div className="modal-dialog modal-dialog-centered">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">
                            {t('tiff_analysis_info', 'TIFF Analysis Information')}
                        </h5>
                        <button
                            type="button"
                            className="btn-close"
                            onClick={onClose}
                            aria-label="Close"
                        ></button>
                    </div>
                    <div className="modal-body">
                        <div className="alert alert-info d-flex align-items-start mb-3">
                            <Info size={20} className="me-2 mt-1 flex-shrink-0" />
                            <div>
                                <p className="mb-2">
                                    <strong>{t('date_range_recommendation', 'Date Range Recommendation')}</strong>
                                </p>
                                <p className="mb-2">
                                    {t('drone_imagery_timing', 'For optimal analysis results, drone imagery should be captured within a date range of 10 to 30 days.')}
                                </p>
                                <p className="mb-0">
                                    {t('tiff_assumption', 'We assume the uploaded TIFF was obtained from drone imagery captured within an appropriate date range.')}
                                </p>
                            </div>
                        </div>

                        <div className="alert alert-warning d-flex align-items-start">
                            <AlertTriangle size={20} className="me-2 mt-1 flex-shrink-0" />
                            <div>
                                <p className="mb-2">
                                    <strong>{t('important_notice', 'Important Notice:')}</strong>
                                </p>
                                <p className="mb-0">
                                    {t('analysis_validity_warning', 'Analysis results may not be valid if the drone imagery was captured outside the recommended date range. Additionally, if cloud coverage exceeds 20% or there are other environmental factors during capture, we recommend using imagery from at least 70 days before the estimated harvest date.')}
                                </p>
                            </div>
                        </div>
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
                            onClick={onConfirm}
                        >
                            {t('confirm_analysis', 'Confirm Analysis')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};