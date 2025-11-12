import { useState, useRef } from "react";
import { FileSpreadsheet, Download, Upload, Loader, CheckCircle, XCircle } from "lucide-react";
import { useTranslation } from "react-i18next";
import {  formatDate } from "../../utils/helpers";
import { Table } from "../common/Table";
import api from "../../utils/api";

export const TemplatesTable = ({templates, onUploadSuccess}) => {
  const { t } = useTranslation("uploader");
  const [uploading, setUploading] = useState(null); // ID del template in upload
  const [downloading, setDownloading] = useState(null); // ID del template in download
  const [uploadStatus, setUploadStatus] = useState(null);
  const fileInputRefs = useRef({});

  const handleFileSelect = async (e, template) => {
    const file = e.target.files[0];
    if (!file) return;

    // Controlla estensione
    const fileName = file.name.toLowerCase();
    if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
      setUploadStatus({
        type: 'error',
        message: t('error_file_type', 'Il file deve essere in formato Excel (.xlsx o .xls)')
      });
      setTimeout(() => setUploadStatus(null), 5000);
      return;
    }

    // Controlla dimensione (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setUploadStatus({
        type: 'error',
        message: t('error_file_size', 'Il file è troppo grande (massimo 10MB)')
      });
      setTimeout(() => setUploadStatus(null), 5000);
      return;
    }

    await uploadFile(file, template);
  };

  const uploadFile = async (file, template) => {
    setUploading(template.id);
    setUploadStatus({ type: 'loading', message: t('uploading', 'Caricamento in corso...') });

    // Usa il nome del template senza estensione come dataset_name
    const datasetName = template.dataset_name.replace(/\.(xlsx|xls)$/i, '');

    const formData = new FormData();
    formData.append('dataset_name', datasetName);
    formData.append('excel_file', file);

    try {
      const data = await api.postFormData('/api/dataset/update/', formData);

      const message = data.message || t('upload_success', 'Caricamento completato con successo!');
      setUploadStatus({ type: 'success', message });

      // Ricarica i template
      if (onUploadSuccess) {
        onUploadSuccess();
      }

      // Reset file input
      if (fileInputRefs.current[template.id]) {
        fileInputRefs.current[template.id].value = '';
      }

      // Cancella messaggio dopo 5 secondi
      setTimeout(() => setUploadStatus(null), 5000);

    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.message || t('upload_error', 'Errore durante il caricamento')
      });

      // Cancella messaggio dopo 8 secondi
      setTimeout(() => setUploadStatus(null), 8000);
    } finally {
      setUploading(null);
    }
  };

  const handleDownload = async (template) => {
    setDownloading(template.dataset_experiment_id);

    try {
      await api.downloadFile(template.download_url, template.filename);
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.message || t('download_error', 'Errore durante il download')
      });
      setTimeout(() => setUploadStatus(null), 8000);
    } finally {
      setDownloading(null);
    }
  };

  const columns = [
    {
      key: "dataset_name",
      render: (value, row) => (
        <div className="d-flex align-items-center justify-content-start">
          <FileSpreadsheet size={32} />
          <strong className="ms-2">{value}</strong>
        </div>
      ),
    },
    {
      key: "last_upload_datetime",
      label: t("last_upload", "Ultimo Upload"),
      className: "align-middle",
      render: (value) => formatDate(value, t),
    },
    {
      key: "actions",
      label: t("actions", "Azioni"),
      className: "text-right align-middle",
      headerClassName: "text-right",
      render: (value, row) => (
        <div className="d-flex gap-2 justify-content-end">
          <button
            className="btn btn-outline-primary btn-sm d-flex align-items-center"
            onClick={() => handleDownload(row)}
            disabled={downloading === row.dataset_experiment_id}
            title={t("download", "Scarica template")}
          >
            {downloading === row.dataset_experiment_id ? (
              <>
                <Loader size={16} className="me-1 spinner-border spinner-border-sm" />
                <span>{t("downloading", "Scaricamento...")}</span>
              </>
            ) : (
              <>
                <Download size={16} className="me-1" />
                <span>{t("download", "Scarica")}</span>
              </>
            )}
          </button>
          <button
            className="btn btn-primary btn-sm d-flex align-items-center"
            onClick={() => fileInputRefs.current[row.id]?.click()}
            disabled={uploading === row.id}
            title={t("upload", "Carica file compilato")}
          >
            {uploading === row.id ? (
              <>
                <Loader size={16} className="me-1 spinner-border spinner-border-sm" />
                <span>{t("uploading", "Caricamento...")}</span>
              </>
            ) : (
              <>
                <Upload size={16} className="me-1" />
                <span>{t("upload", "Carica")}</span>
              </>
            )}
          </button>
          <input
            ref={(el) => (fileInputRefs.current[row.id] = el)}
            type="file"
            accept=".xlsx,.xls"
            style={{ display: 'none' }}
            onChange={(e) => handleFileSelect(e, row)}
            disabled={uploading === row.id}
          />
        </div>
      ),
    },
  ];

  return (
    <>
      <Table
        columns={columns}
        data={templates}
        hover={true}
        className="templates-table"
        emptyState={
          <div className="text-center p-4 text-muted">
            <p>{t("no_templates", "Nessun template disponibile")}</p>
          </div>
        }
      />

      {uploadStatus && (
        <div
          className={`alert alert-${
            uploadStatus.type === 'loading' ? 'info' :
            uploadStatus.type === 'success' ? 'success' :
            'danger'
          } d-flex align-items-center mt-3`}
          role="alert"
        >
          {uploadStatus.type === 'loading' && (
            <Loader size={20} className="me-2 spinner-border spinner-border-sm" />
          )}
          {uploadStatus.type === 'success' && (
            <CheckCircle size={20} className="me-2" />
          )}
          {uploadStatus.type === 'error' && (
            <XCircle size={20} className="me-2" />
          )}
          <span style={{ whiteSpace: 'pre-line' }}>{uploadStatus.message}</span>
        </div>
      )}
    </>
  );
};
