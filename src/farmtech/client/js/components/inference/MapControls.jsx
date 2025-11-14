import { Upload, Route, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import { MapControlButtons } from "./MapControlButtons";
import { TutorialCard } from "./TutorialCard";

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
      Icon: Upload,
      title: t("tutorial_step1_title"),
      description: t("tutorial_step1_desc"),
    },
    {
      key: "step2",
      Icon: Route,
      title: t("tutorial_step2_title"),
      description: t("tutorial_step1_desc"),
    },
    {
      key: "step3",
      Icon: Sparkles,
      title: t("tutorial_step3_title"),
      description: t("tutorial_step1_desc"),
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
        />
      </div>

      {/* Tutorial Container */}
      <div
        className={`tutorial-container position-fixed bottom-0 start-0 end-0 shadow-lg ${isExpanded ? 'tutorial-expanded' : 'tutorial-collapsed'}`}
        style={{
          zIndex: 1000,
          width: "100vw",
          background: "rgba(255, 255, 255, 0.98)",
        }}
      >
        {isExpanded && (
          <div className="h-100 overflow-hidden">
            <div className="h-100 p-2 tutorial-scroll-container">
              <div className="tutorial-cards-wrapper d-flex gap-4">
                {tutorials.map((tutorial) => {
                  return <TutorialCard {...tutorial} key={tutorial.key} />;
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};
