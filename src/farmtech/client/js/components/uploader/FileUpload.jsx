import { useState, useRef } from 'react';
import { CloudUpload, CheckCircle, XCircle, Loader } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';

export const FileUpload = ({templates, onUploadSuccess}) => {
    const { t } = useTranslation('uploader');

    const [dragOver, setDragOver] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null);
    const [lastUploadedFile, setLastUploadedFile] = useState(null);
    const fileInputRef = useRef(null);

    // Debug: log templates to see what we receive
    console.log('Templates received in FileUpload:', templates);

    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(false);

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    };

    const handleFileSelect = (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    };

    const handleFile = async (file) => {
        const fileName = file.name.toLowerCase();

        // Check file extension
        if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
            setUploadStatus({
                type: 'error',
                message: t('error_file_type')
            });
            return;
        }

        // Extract file name without extension
        const fileNameWithoutExt = fileName.replace(/\.(xlsx|xls)$/, '');

        // Check if templates are available
        if (!templates || templates.length === 0) {
            console.error('No templates available:', templates);
            setUploadStatus({
                type: 'error',
                message: t('no_templates')
            });
            return;
        }

        // Check if file name matches one of the available templates
        const templateNames = templates
            .filter(template => template?.name)
            .map(template => {
                // Remove extension from template name to compare
                const templateNameWithoutExt = template.name.replace(/\.(xlsx|xls)$/i, '').toLowerCase();
                return templateNameWithoutExt;
            });

        console.log('File name without extension:', fileNameWithoutExt);
        console.log('Available template names:', templateNames);

        if (templateNames.length === 0) {
            console.error('No valid templates with name found');
            setUploadStatus({
                type: 'error',
                message: t('no_templates')
            });
            return;
        }

        if (!templateNames.includes(fileNameWithoutExt)) {
            setUploadStatus({
                type: 'error',
                message: t('error_template_not_found', {
                    fileName: fileNameWithoutExt,
                    availableTemplates: templateNames.join(', ')
                })
            });
            return;
        }

        // Check file size
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            setUploadStatus({
                type: 'error',
                message: t('error_file_size')
            });
            return;
        }

        // Get the matching template to pass dataset name (using the name without extension)
        const matchingTemplate = templates.find(template => {
            if (!template?.name) return false;
            const templateNameWithoutExt = template.name.replace(/\.(xlsx|xls)$/i, '').toLowerCase();
            return templateNameWithoutExt === fileNameWithoutExt;
        });

        // Use the template name without extension as dataset_name
        const datasetName = matchingTemplate.name.replace(/\.(xlsx|xls)$/i, '');

        await uploadFile(file, datasetName);
    };

    const uploadFile = async (file, datasetName) => {
        setUploading(true);
        setUploadStatus({ type: 'loading', message: t('uploading', 'Caricamento in corso...') });

        const formData = new FormData();
        formData.append('dataset_name', datasetName);
        formData.append('excel_file', file);

        try {
            const data = await api.postFormData('/api/dataset/update/', formData);

            const message = data.message || t('upload_success');
            setUploadStatus({ type: 'success', message });

            // Save last uploaded file name
            setLastUploadedFile(file.name);

            // Reload templates data
            if (onUploadSuccess) {
                onUploadSuccess();
            }

            // Reset file input
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }

            // Clear success message after 5 seconds
            setTimeout(() => {
                setUploadStatus(null);
            }, 5000);

        } catch (error) {
            setUploadStatus({
                type: 'error',
                message: error.message || t('upload_error')
            });

            // Clear error message after 8 seconds
            setTimeout(() => {
                setUploadStatus(null);
            }, 8000);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div>
            <div
                className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{ cursor: 'pointer' }}
            >
                <div className="drop-zone-content">
                    <CloudUpload size={64} className="drop-icon" />
                    <p className="drop-text">
                        {dragOver ? t('drop_here') : t('drop_text')}
                    </p>
                    <p className="drop-hint">
                        {t('drop_hint')}
                    </p>
                    {lastUploadedFile && (
                        <p className="last-upload-info">
                            {t('last_uploaded_file')}: <strong>{lastUploadedFile}</strong>
                        </p>
                    )}
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".xlsx,.xls"
                        style={{ display: 'none' }}
                        onChange={handleFileSelect}
                        disabled={uploading}
                    />
                </div>
            </div>

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
                        <Loader size={20} className="me-2 upload-status-loading" />
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
        </div>
    );
};
