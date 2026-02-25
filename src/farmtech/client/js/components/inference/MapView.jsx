import { useEffect, useRef } from 'react';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import XYZ from 'ol/source/XYZ';
import Draw from 'ol/interaction/Draw';
import Modify from 'ol/interaction/Modify';
import { fromLonLat } from 'ol/proj';
import Feature from 'ol/Feature';
import Polygon from 'ol/geom/Polygon';

export const MapView = ({ tiffFile, isDrawing, onPolygonDrawn, userPolygon, resultPolygon, center, isAnalyzing }) => {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const drawInteractionRef = useRef(null);
    const modifyInteractionRef = useRef(null);
    const vectorSourceRef = useRef(null);
    const resultVectorSourceRef = useRef(null);

    useEffect(() => {
        if (!mapRef.current) return;

        // Initialize vector sources: one for user drawings, one for API results
        vectorSourceRef.current = new VectorSource();
        resultVectorSourceRef.current = new VectorSource();

        // Create map with satellite layer
        const map = new Map({
            target: mapRef.current,
            layers: [
                new TileLayer({
                    source: new XYZ({
                        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                        maxZoom: 19, //TODO: verificare il maxZoom
                        attributions: 'Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                    }),
                }),
                // Layer for API result polygon
                new VectorLayer({
                    source: resultVectorSourceRef.current,
                    style: {
                        'stroke-color': '#ff0000',
                        'stroke-width': 3,
                        'fill-color': 'rgba(255, 0, 0, 0.1)',
                    }
                }),
                // Layer for user-drawn polygon
                new VectorLayer({
                    source: vectorSourceRef.current,
                    style: {
                        'stroke-color': '#00ff00',
                        'stroke-width': 3,
                        'fill-color': 'rgba(0, 255, 0, 0.1)',
                    }
                }),
            ],
            view: new View({
                center: fromLonLat([12.4964, 41.9028]), // Roma
                zoom: 12,
            }),
        });

        mapInstanceRef.current = map;

        // Try to get user's location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const userCoords = fromLonLat([
                        position.coords.longitude,
                        position.coords.latitude
                    ]);
                    map.getView().setCenter(userCoords);
                    map.getView().setZoom(12);
                },
                (error) => {
                    console.error('Geolocation error:', error.message, '- Using default location (Rome)');
                },
                {
                    enableHighAccuracy: false,
                    timeout: 5000,
                    maximumAge: 0
                }
            );
        }

        const handlePolygonChange = (geometry) => {
            const transformedGeometry = geometry.clone().transform('EPSG:3857', 'EPSG:4326');
            onPolygonDrawn(transformedGeometry);
        };

        // Create Draw and Modify interactions once
        const draw = new Draw({
            source: vectorSourceRef.current,
            type: 'Polygon',
        });

        const modify = new Modify({
            source: vectorSourceRef.current,
        });

        // Handle drawend event
        draw.on('drawend', (event) => {
            const feature = event.feature;
            const geometry = feature.getGeometry();

            // Notify parent about the polygon
            handlePolygonChange(geometry);

            // Important: use setTimeout to ensure the drawing finishes cleanly
            // This prevents the mouse from getting stuck and ensures proper rendering
            setTimeout(() => {
                // Clear previous polygons
                vectorSourceRef.current.clear();

                // Add the new feature to the vector source
                vectorSourceRef.current.addFeature(feature);

                // Switch to modify mode
                map.removeInteraction(draw);
                map.addInteraction(modify);
            }, 0);
        });

        // Handle modify event
        modify.on('modifyend', (event) => {
            const features = event.features.getArray();
            if (features.length > 0) {
                const geometry = features[0].getGeometry();
                handlePolygonChange(geometry);
            }
        });

        drawInteractionRef.current = draw;
        modifyInteractionRef.current = modify;

        return () => {
            map.setTarget(null);
        };
    }, [onPolygonDrawn]);

    // Handle drawing state changes
    useEffect(() => {
        if (!mapInstanceRef.current || !drawInteractionRef.current || !modifyInteractionRef.current) return;

        const map = mapInstanceRef.current;
        const draw = drawInteractionRef.current;
        const modify = modifyInteractionRef.current;

        if (isDrawing && !isAnalyzing) {
            // Check if there's already a polygon
            const hasFeatures = vectorSourceRef.current.getFeatures().length > 0;

            if (hasFeatures) {
                // If polygon exists, enable modify mode
                map.removeInteraction(draw);
                map.addInteraction(modify);
            } else {
                // If no polygon, enable draw mode
                map.removeInteraction(modify);
                map.addInteraction(draw);
            }
        } else {
            // Remove both interactions when not in drawing mode or when analyzing
            map.removeInteraction(draw);
            map.removeInteraction(modify);
        }

        return () => {
            // Cleanup on unmount
            map.removeInteraction(draw);
            map.removeInteraction(modify);
        };
    }, [isDrawing, isAnalyzing]);

    // Handle user-drawn polygon display
    useEffect(() => {
        if (!vectorSourceRef.current) return;

        if (!userPolygon) {
            // Clear user polygon from map when state is null
            vectorSourceRef.current.clear();
        }
        // Note: User polygon is added automatically by draw interaction
    }, [userPolygon]);

    // Handle API result polygon display
    useEffect(() => {
        if (!resultVectorSourceRef.current) return;

        if (!resultPolygon) {
            // Clear result polygon from map when state is null
            resultVectorSourceRef.current.clear();
            return;
        }

        // Check if polygon is a GeoJSON object from API (has type and coordinates)
        if (resultPolygon.type === 'Polygon' && resultPolygon.coordinates) {
            // Convert GeoJSON coordinates from EPSG:4326 to EPSG:3857
            const coordinates = resultPolygon.coordinates[0].map(coord =>
                fromLonLat([coord[0], coord[1]])
            );

            // Create OpenLayers polygon geometry
            const polygonGeometry = new Polygon([coordinates]);

            // Create feature and add to map
            const feature = new Feature({
                geometry: polygonGeometry
            });

            // Clear and add new polygon
            resultVectorSourceRef.current.clear();
            resultVectorSourceRef.current.addFeature(feature);
        }
    }, [resultPolygon]);

    useEffect(() => {
        if (tiffFile) {
            console.log('TIFF file loaded:', tiffFile.name);
        }
    }, [tiffFile]);

    // Center map on result polygon when center is provided
    useEffect(() => {
        if (!mapInstanceRef.current || !center) return;

        const map = mapInstanceRef.current;
        const view = map.getView();

        // Convert center coordinates from EPSG:4326 to EPSG:3857
        const centerCoords = fromLonLat([center.lon, center.lat]);

        // Prepare animation options
        const animationOptions = {
            center: centerCoords,
            duration: 1000
        };

        // If TIFF file is used, set zoom to max-1 (18), otherwise keep current zoom
        if (tiffFile) {
            animationOptions.zoom = 18;
        }

        // Animate to center
        view.animate(animationOptions);
    }, [center, tiffFile]);

    return (
        <div className="map-container position-relative" style={{ width: '100%', height: 'calc(100%+90px)', bottom: '-90px' }}>
            <div
                ref={mapRef}
                className="map-view"
                style={{ width: '100%', height: '100%' }}
            />
        </div>
    );
};
