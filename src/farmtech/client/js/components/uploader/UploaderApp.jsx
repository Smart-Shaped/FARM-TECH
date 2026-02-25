import { useState, useEffect } from "react";
import { FileSpreadsheet } from "lucide-react";
import { useTranslation } from "react-i18next";
import { TemplatesTable } from "./TemplatesTable";
import { TutorialSection } from "./TutorialSection";
import api from "../../utils/api";

export const UploaderApp = () => {
  const { t } = useTranslation("uploader");

  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isTutorialExpanded, setIsTutorialExpanded] = useState(true);

  const loadTemplates = async () => {
    try {
      const user = window.__FARMTECH_USER__;
      const data = await api.post("/api/dataset/excel-templates/", {
        group_profile_id: user.group_members?.[0]?.group_profile_id,
      });
      setTemplates(data.templates || []);
      setLoading(false);
    } catch (err) {
      console.error("Error loading templates:", err);
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  if (loading) {
    return (
      <div className="text-center p-4">
        <div className="spinner-border text-primary" role="status">
          <span className="sr-only">{t("loading", "Caricamento...")}</span>
        </div>
        <p className="mt-2">{t("loading", "Caricamento...")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        <strong>{t("error_label", "Errore")}:</strong> {error}
      </div>
    );
  }

  return (
    <div className="container-fluid" style={{ paddingBottom: isTutorialExpanded ? "320px" : "80px" }}>
      <section className="card my-2">
        <div className="card-header">
          <h2 className="h5 mb-0 d-flex align-items-center">
            <FileSpreadsheet size={20} className="me-2" />
            <span>{t("templates_section_title", "Template Excel")}</span>
          </h2>
        </div>
        <div className="card-body">
          <TemplatesTable
            templates={templates}
            onUploadSuccess={loadTemplates}
          />
        </div>
      </section>

      <TutorialSection
        isExpanded={isTutorialExpanded}
        onToggleExpanded={() => setIsTutorialExpanded(!isTutorialExpanded)}
      />
    </div>
  );
};
