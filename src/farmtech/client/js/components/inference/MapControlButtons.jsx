import React, { useRef, useState } from 'react';
import { Upload, X, Route, Sparkles, Loader, HelpCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const MapControlButtons = ({
    tiffFile,
    isDrawing,
    polygon,
    isAnalyzing,
    onTiffUpload,
    onTiffRemove,
    onToggleDrawing,
    onAnalyze,
    onRemovePolygon,
    onToggleTutorial
}) => {
    const { t } = useTranslation('inference');
    const fileInputRef = useRef(null);
    const [uploading, setUploading] = useState(false);

    const drawEnabled = !tiffFile && !isAnalyzing;
    const analyzeEnabled = (tiffFile || polygon) && !isAnalyzing;

    const handleFileSelect = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        //TODO: la verifica del file avviene sia in frontend che in backend?
        if (!file.name.toLowerCase().match(/\.(tiff?|tif)$/)) {
            alert(t('invalid_file_type', 'Please select a valid TIFF file'));
            return;
        }

        setUploading(true);
        //TODO: usare API
        setTimeout(() => {
            onTiffUpload(file);
            setUploading(false);
        }, 500);
    };

    const handleRemoveTiff = () => {
        onTiffRemove();
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleAnalyze = () => {
        onAnalyze();
    };

    const handleDrawClick = () => {
        if (isDrawing && polygon) {
            onRemovePolygon();
        } else {
            onToggleDrawing();
        }
    };

    return (
        <div className="d-flex flex-column align-items-center" style={{ pointerEvents: 'auto' }}>
            <input
                ref={fileInputRef}
                type="file"
                accept=".tiff,.tif"
                style={{ display: 'none' }}
                onChange={handleFileSelect}
            />

            {/* TIFF Info Display */}
            {tiffFile && (
                <div className="mb-3 px-3 py-2 bg-white rounded shadow-sm">
                    <small className="text-muted d-flex align-items-center gap-2">
                        <strong>{tiffFile.name}</strong>
                        <span className="text-primary">({(tiffFile.size / 1024 / 1024).toFixed(2)} MB)</span>
                    </small>
                </div>
            )}

            {/* Controls */}
            <div className="d-flex gap-3 align-items-center map-controls">
                {/* TIFF Upload Button */}
                <button
                    className={`btn ${tiffFile ? 'btn-primary' : 'btn-light'} shadow-sm d-flex align-items-center justify-content-center rounded-circle`}
                    style={{ width: '56px', height: '56px' }}
                    onClick={tiffFile ? handleRemoveTiff : () => fileInputRef.current?.click()}
                    title={tiffFile ? t('remove_tiff', 'Remove TIFF') : t('upload_tiff', 'Upload TIFF')}
                    disabled={uploading || (isDrawing || polygon)}
                >
                    {uploading ? (
                        <Loader size={24} className="upload-status-loading" />
                    ) : tiffFile ? (
                        <X size={24} />
                    ) : (
                        <Upload size={24} />
                    )}
                </button>

                {/* Draw Polygon Button */}
                <button
                    className={`btn ${(isDrawing || polygon) ? 'btn-primary' : 'btn-light'} shadow-sm d-flex align-items-center justify-content-center rounded-circle`}
                    style={{ width: '56px', height: '56px' }}
                    onClick={handleDrawClick}
                    title={t('draw_polygon', 'Draw Polygon')}
                    disabled={!drawEnabled}
                >
                    {(isDrawing || polygon) ? <X size={24} /> : <Route size={24} />}
                </button>

                {/* Analyze Button */}
                <button
                    className="btn btn-light shadow-sm d-flex align-items-center justify-content-center rounded-circle position-relative"
                    style={{ width: '56px', height: '56px' }}
                    onClick={handleAnalyze}
                    title={t('analyze', 'Analyze')}
                    disabled={!analyzeEnabled}
                >
                    {isAnalyzing ? (
                        <Loader size={24} className="upload-status-loading" />
                    ) : (
                        <Sparkles size={24} />
                    )}
                </button>

                {/* Help/Tutorial Button */}
                <button
                    className="btn btn-light shadow-sm d-flex align-items-center justify-content-center rounded-circle"
                    style={{ width: '56px', height: '56px' }}
                    onClick={onToggleTutorial}
                    title={t('help', 'Help')}
                >
                    <HelpCircle size={24} />
                </button>
            </div>
        </div>
    );
};