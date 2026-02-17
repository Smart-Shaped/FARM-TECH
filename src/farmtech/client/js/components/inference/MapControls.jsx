import { Upload, Route, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import { MapControlButtons } from "./MapControlButtons";

export const MapControls = ({
  tiffFile,
  isDrawing,
  polygon,
  isAnalyzing,
  onTiffUpload,
  onTiffRemove,
  onToggleDrawing,
  onAnalyze,
  onRemovePolygon,
  isExpanded,
  onToggleExpanded,
}) => {
  const { t } = useTranslation("inference");

  const tutorials = [
    {
      key: "step1",
      Icon: Route,
      title: t("usage_draw_polygon"),
      description: t("usage_draw_polygon_desc"),
    },
    {
      key: "step2",
      Icon: Upload,
      title: t("usage_upload_tiff"),
      description: t("usage_upload_tiff_desc"),
    },
    {
      key: "step3",
      Icon: Sparkles,
      title: t("usage_ai_algorithm"),
      description: t("usage_ai_algorithm_desc"),
    },
  ];


  return (
    <>
      <div
        className={`tutorial-controls-container position-fixed bottom-0 d-flex justify-content-center w-100 ${isExpanded ? 'controls-raised' : ''}`}
        style={{
          zIndex: 1001,
          pointerEvents: "none",
          marginBottom: "1rem",
        }}
      >
        <MapControlButtons
          tiffFile={tiffFile}
          isDrawing={isDrawing}
          polygon={polygon}
          isAnalyzing={isAnalyzing}
          onTiffUpload={onTiffUpload}
          onTiffRemove={onTiffRemove}
          onToggleDrawing={onToggleDrawing}
          onAnalyze={onAnalyze}
          onRemovePolygon={onRemovePolygon}
          onToggleTutorial={onToggleExpanded}
          isTutorialExpanded={isExpanded}
        />
      </div>

      {/* Tutorial Container */}
      <div
        className={`tutorial-container position-fixed start-0 end-0 shadow-lg ${isExpanded ? 'tutorial-expanded' : 'tutorial-collapsed'}`}
        style={{
          zIndex: 1000,
          width: "100vw",
          background: "rgba(255, 255, 255, 0.98)",
          maxHeight: isExpanded ? "300px" : "0",
          overflow: "hidden",
          transition: "max-height 0.3s ease-in-out",
          bottom: "4px",
        }}
      >
        {/* Features Section */}
        {isExpanded && (
          <div className="h-100">
            <div
              className="p-3 tutorial-scroll-container-vertical"
              style={{
                height: "100%",
                overflowY: "scroll",
              }}
            >
              <ol className="tutorial-steps-list mb-0">
                {tutorials.map((tutorial) => (
                  <li key={tutorial.key} className="mb-4">
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
                        <tutorial.Icon size={20} />
                      </div>
                      <div>
                        <h4 className="h5 mb-1 fw-bold">{tutorial.title}</h4>
                        <p className="text-muted mb-0">{tutorial.description}</p>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}
      </div>
    </>
  );
};
