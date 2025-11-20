import React, { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { MapView } from "./MapView";
import { DateSelectionDialog } from "./DateSelectionDialog";
import { TiffInfoDialog } from "./TiffInfoDialog";
import { MapControls } from "./MapControls";
import api from "../../utils/api";
import { YieldResultCard } from "./YieldResultCard";
import { AnalysisProgressBar } from "./AnalysisProgressBar";

export const InferenceApp = ({ hasPermission = false }) => {
  const { t } = useTranslation("inference");
  const [tiffFile, setTiffFile] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [polygon, setPolygon] = useState(null);
  const [showDateDialog, setShowDateDialog] = useState(false);
  const [showTiffInfoDialog, setShowTiffInfoDialog] = useState(false);
  const [isTutorialExpanded, setIsTutorialExpanded] = useState(true);
  const [savedDates, setSavedDates] = useState({ startDate: "", endDate: "" });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const progressIntervalRef = useRef(null);

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);

  const handleRemovePolygon = () => {
    setPolygon(null);
    setIsDrawing(false);
  };

  const handleAnalysisAPI = async (data) => {
    setIsAnalyzing(true);
    setAnalysisResult(null);
    setAnalysisProgress(0);

    // Clear any existing interval
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }

    try {
      let response = undefined;

      if (data.tiffFile) {
        // For TIFF upload, track real upload progress
        const formData = new FormData();
        formData.append("tiff_file", data.tiffFile);

        response = await api.postFormData(
          "/api/inference/trigger/",
          formData,
          {},
          (uploadProgress) => {
            // Upload is 50% of total progress, processing is the other 50%
            setAnalysisProgress(uploadProgress / 2);
          }
        );

        // After upload completes, simulate processing progress from 50% to 90%
        let currentProgress = 50;
        progressIntervalRef.current = setInterval(() => {
          currentProgress += 2;
          if (currentProgress >= 90) {
            clearInterval(progressIntervalRef.current);
            currentProgress = 90;
          }
          setAnalysisProgress(currentProgress);
        }, 100);
      }

      if (data.polygon && data.startDate && data.endDate) {
        // For polygon analysis, simulate progress
        setAnalysisProgress(10);

        progressIntervalRef.current = setInterval(() => {
          setAnalysisProgress(prev => {
            const next = prev + 3;
            if (next >= 50) {
              clearInterval(progressIntervalRef.current);
              return 90;
            }
            return next;
          });
        }, 150);

        const coordinates = data.polygon.getCoordinates();
        const body = {
          polygon: {type: 'Polygon', coordinates},
          start_date: data.startDate,
          end_date: data.endDate,
        };
        response = await api.post("/api/inference/trigger/", body);
      }

      // Clear interval when done
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }

      // Complete progress
      setAnalysisProgress(100);

      // Success - result contains yield and polygon
      let { result, unit, polygon: resultPolygon, center } = response;
      let warning = null;

      // Check for negative result
      if (result < 0) {
        result = 0;
        warning = t(
          "analysis_warning",
          "Il risultato è negativo. Verifica che le date siano nel range corretto o che il TIFF contenga le bande necessarie nell'ordine: Blue, Green, Red, Near Red, NIR."
        );
      }

      setAnalysisResult({
        yield: `${(result/1000).toFixed(2)} ${unit}`,
        polygon: resultPolygon,
        center,
        warning
      });
    } catch (error) {
      console.error("Analysis failed:", error);

      // Clear interval on error
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }

      // Show error with disclaimer
      setAnalysisResult({
        yield: "0 ton",
        polygon: null,
        center: null,
        warning: t(
          "analysis_error",          
        )
      });
    } finally {
      setIsAnalyzing(false);
      // Reset progress after a short delay
      setTimeout(() => setAnalysisProgress(0), 500);
    }
  };

  if (!hasPermission) {
    return (
      <div className="container-fluid py-5 text-center">
        <div className="alert alert-warning">
          <h4>{t("no_permission_title")}</h4>
          <p>
            {t(
              "no_permission_message",
            )}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="inference-app" style={{ position: "relative" }}>
      {analysisResult && (
        <YieldResultCard
          yield={analysisResult.yield}
          onClose={() => setAnalysisResult(null)}
          warning={analysisResult.warning}
        />
      )}

      <MapView
        tiffFile={tiffFile}
        isDrawing={isDrawing}
        onPolygonDrawn={setPolygon}
        userPolygon={polygon}
        resultPolygon={analysisResult?.polygon}
        center={analysisResult?.center}
        isAnalyzing={isAnalyzing}
      />

      <MapControls
        tiffFile={tiffFile}
        isDrawing={isDrawing}
        polygon={polygon}
        isAnalyzing={isAnalyzing}
        onTiffUpload={(file) => {
          setTiffFile(file);
        }}
        onTiffRemove={() => {
          setTiffFile(null);
          setPolygon(null);
          setAnalysisResult(null);
        }}
        onToggleDrawing={() => setIsDrawing(!isDrawing)}
        onAnalyze={() => {
          if (tiffFile) {
            setShowTiffInfoDialog(true);
          } else {
            setShowDateDialog(true);
          }
        }}
        onRemovePolygon={() => {
          handleRemovePolygon();
          setAnalysisResult(null);
        }}
        isExpanded={isTutorialExpanded}
        onToggleExpanded={() => setIsTutorialExpanded(!isTutorialExpanded)}
      />

      {showDateDialog && (
        <DateSelectionDialog
          onClose={() => setShowDateDialog(false)}
          onConfirm={(startDate, endDate) => {
            setSavedDates({ startDate, endDate });
            setShowDateDialog(false);
            handleAnalysisAPI({ startDate, endDate, polygon });
          }}
          initialStartDate={savedDates.startDate}
          initialEndDate={savedDates.endDate}
        />
      )}

      {showTiffInfoDialog && (
        <TiffInfoDialog
          onClose={() => setShowTiffInfoDialog(false)}
          onConfirm={() => {
            setShowTiffInfoDialog(false);
            handleAnalysisAPI({ tiffFile });
          }}
        />
      )}

      {isAnalyzing && <AnalysisProgressBar progress={analysisProgress} />}
    </div>
  );
};
