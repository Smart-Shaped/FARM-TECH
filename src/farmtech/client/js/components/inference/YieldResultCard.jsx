import { X, TrendingUp, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const YieldResultCard = ({ yield: yieldValue, onClose, warning }) => {
    const { t } = useTranslation('inference');

    return (
        <div className="yield-result-card card shadow-lg border-0" style={{
            position: 'absolute',
            top: '70px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
            minWidth: '300px',
            maxWidth: '400px'
        }}>
            <div className="card-body p-3">
                <div className="d-flex justify-content-between align-items-start mb-2">
                    <div className="d-flex align-items-center gap-2">
                        <div
                            className="rounded-circle d-flex align-items-center justify-content-center"
                            style={{
                                width: '36px',
                                height: '36px',
                                background: 'linear-gradient(135deg, var(--gn-primary-dark, #2e5f7d) 0%, var(--gn-primary, #397aab) 100%)',
                            }}
                        >
                            <TrendingUp size={20} className="text-white" />
                        </div>
                        <div className="mb-0 fw-bold fs-5">
                            {t('yield_result', 'Risultato Analisi')}
                        </div>
                    </div>
                    <button
                        className="btn btn-sm btn-link text-muted p-0"
                        onClick={onClose}
                        title={t('close', 'Close')}
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="text-center py-3">
                    <div className="display-3 fw-bold text-primary mb-1">
                        {yieldValue}
                    </div>
                </div>

                {warning && (
                    <div className="alert alert-warning mb-0 d-flex align-items-start gap-2" style={{ fontSize: '0.85rem' }}>
                        <AlertTriangle size={18} className="flex-shrink-0 mt-1" />
                        <div>{warning}</div>
                    </div>
                )}
            </div>
        </div>
    );
};
