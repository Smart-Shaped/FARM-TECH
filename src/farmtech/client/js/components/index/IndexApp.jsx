import { useTranslation, Trans } from 'react-i18next';
import { Route, Upload, Sparkles, CheckCircle } from 'lucide-react';

export const IndexApp = ({ staticUrl = '' }) => {
    const { t } = useTranslation('index');

    return (
      <div className="gn-theme gn-homepage">
      {/* Hero Section */}
      <section className="hero-gradient text-white py-5">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-lg-8 text-center">
              <p className="lead fs-4">{t("hero_description")}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Project Description */}
      <section className="py-5 bg-light">
        <div className="container">
          <h2 className="text-center mb-5 fw-bold">{t("section_project")}</h2>
          <div className="row g-4">
            <div className="col-md-6">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body p-4">
                  <h3 className="card-title h5 fw-bold mb-3">{t("project_innovative_solution")}</h3>
                  <p className="card-text">{t("project_description")}</p>
                </div>
              </div>
            </div>
            <div className="col-md-6">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body p-4">
                  <h3 className="card-title h5 fw-bold mb-3">{t("project_main_features")}</h3>
                  <ul className="list-unstyled">
                    <li className="mb-2 d-flex align-items-center"><CheckCircle size={20} className="text-success me-2" />{t("feature_polygon_drawing")}</li>
                    <li className="mb-2 d-flex align-items-center"><CheckCircle size={20} className="text-success me-2" />{t("feature_tiff_upload")}</li>
                    <li className="mb-2 d-flex align-items-center"><CheckCircle size={20} className="text-success me-2" />{t("feature_ai_inference")}</li>
                    <li className="mb-2 d-flex align-items-center"><CheckCircle size={20} className="text-success me-2" />{t("feature_yield_estimation")}</li>
                    <li className="mb-2 d-flex align-items-center"><CheckCircle size={20} className="text-success me-2" />{t("feature_research_visualization")}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-5">
        <div className="container">
          <h2 className="text-center mb-5 fw-bold">{t("section_usage_modes")}</h2>
          <div className="row g-4">
            <div className="col-lg-4 col-md-6">
              <div className="card h-100 border-0 shadow-sm text-center">
                <div className="card-body p-4">
                  <div className="feature-icon-gradient">
                    <Route size={40} />
                  </div>
                  <h3 className="card-title h5 fw-bold mb-3">{t("usage_draw_polygon")}</h3>
                  <p className="card-text text-muted">{t("usage_draw_polygon_desc")}</p>
                </div>
              </div>
            </div>
            <div className="col-lg-4 col-md-6">
              <div className="card h-100 border-0 shadow-sm text-center">
                <div className="card-body p-4">
                  <div className="feature-icon-gradient">
                    <Upload size={40} />
                  </div>
                  <h3 className="card-title h5 fw-bold mb-3">{t("usage_upload_tiff")}</h3>
                  <p className="card-text text-muted">{t("usage_upload_tiff_desc")}</p>
                </div>
              </div>
            </div>
            <div className="col-lg-4 col-md-6">
              <div className="card h-100 border-0 shadow-sm text-center">
                <div className="card-body p-4">
                  <div className="feature-icon-gradient">
                    <Sparkles size={40} />
                  </div>
                  <h3 className="card-title h5 fw-bold mb-3">{t("usage_ai_algorithm")}</h3>
                  <p className="card-text text-muted">{t("usage_ai_algorithm_desc")}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-5 bg-light">
        <div className="container">
          <h2 className="text-center mb-5 fw-bold">{t("section_how_it_works")}</h2>
          <div className="row g-4">
            <div className="col-lg-4">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body p-4">
                  <div className="step-number-circle" style={{fontSize: '24px', fontWeight: 'bold'}}>
                    1
                  </div>
                  <h3 className="card-title h5 fw-bold mb-3">{t("step_area_selection")}</h3>
                  <p className="card-text mb-2">{t("step_area_selection_desc")}</p>
                  <p className="card-text text-muted small">{t("step_area_selection_note")}</p>
                </div>
              </div>
            </div>
            <div className="col-lg-4">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body p-4">
                  <div className="step-number-circle" style={{fontSize: '24px', fontWeight: 'bold'}}>
                    2
                  </div>
                  <h3 className="card-title h5 fw-bold mb-3">{t("step_ai_processing")}</h3>
                  <p className="card-text">{t("step_ai_processing_desc")}</p>
                </div>
              </div>
            </div>
            <div className="col-lg-4">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body p-4">
                  <div className="step-number-circle" style={{fontSize: '24px', fontWeight: 'bold'}}>
                    3
                  </div>
                  <h3 className="card-title h5 fw-bold mb-3">{t("step_results")}</h3>
                  <p className="card-text">{t("step_results_desc")}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Bando e Partnership */}
      <section className="py-5">
        <div className="container">
          <h2 className="text-center mb-5 fw-bold">{t("section_funding")}</h2>

          <div className="mb-5 overflow-hidden">
            <div className="funding-logos-track">
              {/* Primo set di loghi */}
              <a href="/" className="d-inline-block flex-shrink-0">
                <img src={`${staticUrl}img/TRC_logo_orizzontale.svg`} alt="Logo Tech4You" className="img-fluid" style={{maxHeight: '80px'}} />
              </a>
              <a href="/" className="d-inline-block flex-shrink-0">
                <img src={`${staticUrl}img/TRC_logo_orizzontale.svg`} alt="Logo Partner 1" className="img-fluid" style={{maxHeight: '80px'}} />
              </a>
              <a href="/" className="d-inline-block flex-shrink-0">
                <img src={`${staticUrl}img/TRC_logo_orizzontale.svg`} alt="Logo Partner 2" className="img-fluid" style={{maxHeight: '80px'}} />
              </a>
              <a href="/" className="d-inline-block flex-shrink-0">
                <img src={`${staticUrl}img/TRC_logo_orizzontale.svg`} alt="Logo Partner 3" className="img-fluid" style={{maxHeight: '80px'}} />
              </a>
              {/* Duplica i loghi per loop continuo */}
              <a href="/" className="d-inline-block flex-shrink-0">
                <img src={`${staticUrl}img/TRC_logo_orizzontale.svg`} alt="Logo Tech4You" className="img-fluid" style={{maxHeight: '80px'}} />
              </a>
              <a href="/" className="d-inline-block flex-shrink-0">
                <img src={`${staticUrl}img/TRC_logo_orizzontale.svg`} alt="Logo Partner 1" className="img-fluid" style={{maxHeight: '80px'}} />
              </a>
              <a href="/" className="d-inline-block flex-shrink-0">
                <img src={`${staticUrl}img/TRC_logo_orizzontale.svg`} alt="Logo Partner 2" className="img-fluid" style={{maxHeight: '80px'}} />
              </a>
              <a href="/" className="d-inline-block flex-shrink-0">
                <img src={`${staticUrl}img/TRC_logo_orizzontale.svg`} alt="Logo Partner 3" className="img-fluid" style={{maxHeight: '80px'}} />
              </a>
            </div>
          </div>

          <div className="row justify-content-center">
            <div className="col-lg-8">
              <div className="card border-0 shadow-sm">
                <div className="card-body p-4">
                  <p className="lead mb-4">
                    <Trans i18nKey="funding_description" ns="index" components={{ strong: <strong /> }} />
                  </p>
                  <div className="row g-3 mb-4">
                    <div className="col-md-6">
                      <div className="d-flex flex-column">
                        <span className="text-muted small mb-1">{t("funding_id_code")}</span>
                        <span className="fw-bold fs-5">ECS00000009</span>
                      </div>
                    </div>
                    <div className="col-md-6">
                      <div className="d-flex flex-column">
                        <span className="text-muted small mb-1">{t("funding_cup")}</span>
                        <span className="fw-bold fs-5">C33C22000290006</span>
                      </div>
                    </div>
                  </div>
                  <p className="text-muted small mb-0">{t("funding_legal")}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
    )
}