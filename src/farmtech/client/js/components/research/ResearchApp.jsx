import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ExternalLink } from 'lucide-react';
import api from '../../utils/api' 
export const ResearchApp = () => {
    const { t } = useTranslation('research');
    const [researchLines, setResearchLines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchResearchLines();
    }, []);

    const fetchResearchLines = async () => {
        try {
            setLoading(true);
            const response = await api.get('/api/group/list/');
            if (!response.success) {
                throw new Error('Failed to fetch research lines');
            }
            setResearchLines(response.groups || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleViewDashboard = (line) => {
        // Naviga su dashboard usando l'ID della linea di ricerca cliccata
        window.location.href = `/catalogue/#/dashboard/${encodeURIComponent(line.dashboard_id)}`;
    };

    return (
        <div className="gn-theme gn-homepage">
            <div className="container py-5">
                <div className="mb-5 text-center">
                    <h1 className="h2 fw-bold mb-2">{t('page_title')}</h1>
                    <p className="text-muted">{t('page_subtitle')}</p>
                </div>

                {loading && (
                    <div className="text-center py-5">
                        <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">{t('loading')}</span>
                        </div>
                        <p className="mt-3 text-muted">{t('loading')}</p>
                    </div>
                )}

                {error && (
                    <div className="alert alert-danger" role="alert">
                        {t('error_loading')}: {error}
                    </div>
                )}

                {!loading && !error && researchLines.length === 0 && (
                    <div className="alert alert-info" role="alert">
                        {t('no_research_lines')}
                    </div>
                )}

                {!loading && !error && researchLines.length > 0 && (
                    <div className="card border-0 shadow-sm">
                        <div className="card-body p-0">
                            <div className="table-responsive">
                                <table className="table table-hover mb-0">
                                    <thead className="table-light">
                                        <tr>
                                            <th className="px-4 py-3">{t('table_name')}</th>
                                            <th className="px-4 py-3 text-end">{t('table_actions')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {researchLines.map((line) => (
                                            <tr
                                                key={line.id}
                                                style={{cursor: 'pointer'}}
                                                onClick={() => handleViewDashboard(line)}
                                            >
                                                <td className="px-4 py-3">
                                                    <div className="fw-medium">{line.title}</div>
                                                </td>
                                                <td className="px-4 py-3 text-end">
                                                    <button
                                                        className="btn btn-sm btn-primary d-inline-flex align-items-center gap-2"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleViewDashboard(line);
                                                        }}
                                                    >
                                                        {t('view_dashboard')}
                                                        <ExternalLink size={16} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
