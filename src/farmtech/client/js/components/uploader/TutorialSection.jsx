import { Download, FileEdit, Upload, CheckCircle, HelpCircle } from "lucide-react";
import { useTranslation } from "react-i18next";

export const TutorialSection = ({ isExpanded, onToggleExpanded }) => {
  const { t } = useTranslation("uploader");

  return (
    <>
      {/* Floating Help Button */}
      <div
        className="position-fixed"
        style={{
          bottom: isExpanded ? "316px" : "20px",
          right: "20px",
          zIndex: 1001,
          transition: "bottom 0.3s ease-in-out",
        }}
      >
        <button
          className="btn btn-primary shadow-lg d-flex align-items-center justify-content-center rounded-circle"
          style={{ width: "56px", height: "56px" }}
          onClick={onToggleExpanded}
          title={t("help", "Aiuto")}
        >
          <HelpCircle size={24} />
        </button>
      </div>

      {/* Tutorial Container */}
      <div
        className={`tutorial-container position-fixed start-0 end-0 shadow-lg ${
          isExpanded ? "tutorial-expanded" : "tutorial-collapsed"
        }`}
        style={{
          zIndex: 1000,
          width: "100%",
          background: "rgba(255, 255, 255, 0.98)",
          maxHeight: isExpanded ? "300px" : "0",
          overflow: "hidden",
          transition: "max-height 0.3s ease-in-out",
          bottom: '4px'
        }}
      >
        {isExpanded && (
          <div className="h-100">
            <div
              className="p-3 tutorial-scroll-container-vertical"
              style={{
                height: '100%',
                overflowY: "scroll",
              }}
            >
              <ol className="tutorial-steps-list mb-0">
                <li className="mb-4">
                  <div className="d-flex align-items-start gap-3">
                    <div
                      className="tutorial-icon text-white rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                      style={{
                        width: "40px",
                        height: "40px",
                        background:
                          "linear-gradient(135deg, var(--gn-primary-dark, #2e5f7d) 0%, var(--gn-primary, #397aab) 100%)",
                      }}
                    >
                      <Download size={20} />
                    </div>
                    <div>
                      <h4 className="h5 mb-1 fw-bold">
                        {t("tutorial_step1_title")}
                      </h4>
                      <p className="text-muted mb-0">
                        {t("tutorial_step1_desc")}
                      </p>
                    </div>
                  </div>
                </li>

                <li className="mb-4">
                  <div className="d-flex align-items-start gap-3">
                    <div
                      className="tutorial-icon text-white rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                      style={{
                        width: "40px",
                        height: "40px",
                        background:
                          "linear-gradient(135deg, var(--gn-primary-dark, #2e5f7d) 0%, var(--gn-primary, #397aab) 100%)",
                      }}
                    >
                      <FileEdit size={20} />
                    </div>
                    <div>
                      <h4 className="h5 mb-1 fw-bold">
                        {t("tutorial_step2_title")}
                      </h4>
                      <p className="text-muted mb-2">
                        {t("tutorial_step2_desc")}
                      </p>
                      <ul className="text-muted small mb-0">
                        <li>{t("tutorial_step2_item1")}</li>
                        <li>{t("tutorial_step2_item2")}</li>
                        <li>{t("tutorial_step2_item3")}</li>
                      </ul>
                    </div>
                  </div>
                </li>

                <li className="mb-4">
                  <div className="d-flex align-items-start gap-3">
                    <div
                      className="tutorial-icon text-white rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                      style={{
                        width: "40px",
                        height: "40px",
                        background:
                          "linear-gradient(135deg, var(--gn-primary-dark, #2e5f7d) 0%, var(--gn-primary, #397aab) 100%)",
                      }}
                    >
                      <Upload size={20} />
                    </div>
                    <div>
                      <h4 className="h5 mb-1 fw-bold">
                        {t("tutorial_step3_title")}
                      </h4>
                      <p className="text-muted mb-0">
                        {t("tutorial_step3_desc")}
                      </p>
                    </div>
                  </div>
                </li>

                <li className="mb-2">
                  <div className="d-flex align-items-start gap-3">
                    <div
                      className="tutorial-icon text-white rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                      style={{
                        width: "40px",
                        height: "40px",
                        background:
                          "linear-gradient(135deg, var(--gn-primary-dark, #2e5f7d) 0%, var(--gn-primary, #397aab) 100%)",
                      }}
                    >
                      <CheckCircle size={20} />
                    </div>
                    <div>
                      <h4 className="h5 mb-1 fw-bold">
                        {t("tutorial_step4_title")}
                      </h4>
                      <p className="text-muted mb-2">
                        {t("tutorial_step4_desc")}
                      </p>
                      <div className="alert alert-info small mb-0 py-2">
                        <strong>{t("tutorial_step4_note_title")}</strong>{" "}
                        {t("tutorial_step4_note_desc")}
                      </div>
                    </div>
                  </div>
                </li>
              </ol>
            </div>
          </div>
        )}
      </div>
    </>
  );
};
