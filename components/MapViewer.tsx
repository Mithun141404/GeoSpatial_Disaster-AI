import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { AnalysisResult } from '../types';
import L from 'leaflet';
import { MapContainer, TileLayer, GeoJSON, ZoomControl, useMap } from 'react-leaflet';
import { Split, Maximize, X, ShieldAlert, Target, ExternalLink, Info, Activity, Globe, MousePointer2, LayoutList } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface MapViewerProps {
  analysisResult: AnalysisResult | null;
  theme: 'light' | 'dark';
}

const SEVERITY_COLORS = {
  High: '#ef4444', // Red-500
  Medium: '#f97316', // Orange-500
  Low: '#3b82f6', // Blue-500
  Default: '#64748b' // Slate-500
};

const MapController: React.FC<{ result: AnalysisResult | null }> = ({ result }) => {
  const map = useMap();
  useEffect(() => {
    if (result?.geospatialData?.features?.length) {
      try {
        const geoJsonLayer = L.geoJSON(result.geospatialData as any);
        const bounds = geoJsonLayer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [80, 80], maxZoom: 14, animate: true });
        }
      } catch (e) {
        console.error("Map fitBounds failed:", e);
      }
    }
  }, [result, map]);
  return null;
};

const InteractiveGeoJson: React.FC<{ 
  data: any; 
  onSelect: (props: any) => void;
  onOpenModal: (props: any) => void;
}> = ({ data, onSelect, onOpenModal }) => {
  const map = useMap();

  const getStyle = (feature: any): L.PathOptions => {
    const severity = feature?.properties?.severity || 'Default';
    const color = SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.Default;
    return {
      color: color,
      weight: 2,
      fillOpacity: 0.35,
      fillColor: color,
      lineCap: 'round',
      lineJoin: 'round',
      className: 'hover-glow'
    };
  };

  const onEachFeature = useCallback((feature: any, layer: L.Layer) => {
    if (layer instanceof L.Path) {
      const props = feature.properties || {};
      const severity = props.severity || 'Low';
      const color = SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.Default;
      const name = props.name || "Identified Zone";
      const tooltipId = `details-btn-${name.replace(/[^a-zA-Z0-9]/g, '-')}`;
      
      const container = L.DomUtil.create('div', 'tooltip-content');
      container.className = "bg-slate-950/98 backdrop-blur-xl px-4 py-4 rounded-2xl border shadow-2xl text-white min-w-[220px]";
      container.style.borderColor = `${color}44`;
      
      container.innerHTML = `
        <div class="flex items-center justify-between mb-2">
          <div class="text-[10px] font-black uppercase tracking-widest" style="color: ${color}">
            ${severity} Severity
          </div>
          <div class="text-[9px] px-1.5 py-0.5 rounded border font-mono" style="background: ${color}22; color: ${color}; border-color: ${color}22">
            ${props.confidence || '98%'}
          </div>
        </div>
        <div class="text-sm font-bold text-slate-100 mb-1">${name}</div>
        <div class="text-[9px] text-slate-500 font-bold uppercase mb-3 flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full animate-pulse" style="background-color: ${color}"></span>
          Boundary Validated
        </div>
        <button id="${tooltipId}" class="flex items-center justify-center space-x-2 w-full py-2 transition-all rounded-xl text-[10px] font-bold text-white shadow-lg border" style="background-color: ${color}; border-color: ${color}44">
          <span>INVESTIGATE AREA</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
        </button>
      `;

      layer.on('tooltipopen', () => {
        const btn = document.getElementById(tooltipId);
        if (btn) {
          L.DomEvent.on(btn, 'click', (e: Event) => {
            L.DomEvent.stopPropagation(e);
            onOpenModal(props);
          });
        }
      });

      layer.bindTooltip(container, { 
        sticky: true, 
        direction: 'top', 
        offset: [0, -15], 
        opacity: 1,
        interactive: true 
      });

      layer.on({
        mouseover: (e) => {
          const l = e.target as L.Path;
          l.setStyle({ 
            weight: 4, 
            fillOpacity: 0.55
          });
          l.bringToFront();
        },
        mouseout: (e) => {
          const l = e.target as L.Path;
          l.setStyle(getStyle(feature));
        },
        click: (e) => {
          const l = e.target as any;
          L.DomEvent.stopPropagation(e);
          if (l.getBounds) {
            map.flyToBounds(l.getBounds(), { padding: [80, 80], duration: 1 });
          }
          onSelect(props);
        }
      });
    }
  }, [map, onSelect, onOpenModal]);

  return <GeoJSON data={data} style={getStyle} onEachFeature={onEachFeature} />;
};

const MapLegend = ({ theme }: { theme: 'light' | 'dark' }) => (
  <div className="absolute bottom-6 right-6 z-[1000] bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl min-w-[160px]">
    <div className="flex items-center space-x-2 mb-3 border-b border-slate-100 dark:border-slate-800 pb-2">
      <LayoutList className="w-3.5 h-3.5 text-slate-500" />
      <span className="text-[10px] font-black uppercase tracking-widest text-slate-700 dark:text-slate-300">Criticality</span>
    </div>
    <div className="space-y-2.5">
      {[
        { label: 'High Severity', color: SEVERITY_COLORS.High },
        { label: 'Medium Severity', color: SEVERITY_COLORS.Medium },
        { label: 'Low Severity', color: SEVERITY_COLORS.Low }
      ].map((item) => (
        <div key={item.label} className="flex items-center space-x-3">
          <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: item.color }}></div>
          <span className="text-[10px] font-bold text-slate-600 dark:text-slate-400">{item.label}</span>
        </div>
      ))}
    </div>
  </div>
);

export const MapViewer: React.FC<MapViewerProps> = ({ analysisResult, theme }) => {
  const [viewMode, setViewMode] = useState<'standard' | 'split'>('standard');
  const [selectedFeature, setSelectedFeature] = useState<any | null>(null);
  const [modalFeature, setModalFeature] = useState<any | null>(null);

  const darkTiles = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
  const lightTiles = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png";

  return (
    <div className="relative w-full h-full bg-slate-100 dark:bg-slate-900 overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl transition-colors">
      <div className="absolute top-4 right-4 z-[1000] flex flex-col space-y-2">
        <div className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-md p-1.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col space-y-1 shadow-2xl">
          <button 
            onClick={() => setViewMode('standard')}
            className={`p-2.5 rounded-lg transition-all ${viewMode === 'standard' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'}`}
          >
            <Maximize className="w-4 h-4" />
          </button>
          <button 
            onClick={() => setViewMode('split')}
            className={`p-2.5 rounded-lg transition-all ${viewMode === 'split' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'}`}
          >
            <Split className="w-4 h-4" />
          </button>
        </div>
      </div>

      <AnimatePresence>
        {modalFeature && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-[2000] flex items-center justify-center p-6 bg-slate-950/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-3xl shadow-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col transition-colors"
            >
              <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
                <div className="flex items-center space-x-4">
                  <div className="p-3 bg-blue-600 rounded-2xl shadow-lg shadow-blue-900/40" style={{ backgroundColor: SEVERITY_COLORS[modalFeature.severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.Default }}>
                    <Target className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-xl font-black text-slate-900 dark:text-white tracking-tight">{modalFeature.name}</h2>
                    <p className="text-[10px] font-black uppercase tracking-[0.2em]" style={{ color: SEVERITY_COLORS[modalFeature.severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.Default }}>
                      {modalFeature.severity} Criticality Analysis
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => setModalFeature(null)}
                  className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full text-slate-400 hover:text-slate-900 dark:hover:text-white transition-all border border-transparent hover:border-slate-200 dark:hover:border-slate-700"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-8 space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-50 dark:bg-slate-800/40 p-5 rounded-2xl border border-slate-200 dark:border-slate-700/50">
                    <div className="flex items-center space-x-2 text-slate-500 mb-2">
                      <Activity className="w-4 h-4" />
                      <span className="text-[10px] font-black uppercase tracking-widest">Confidence</span>
                    </div>
                    <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 tracking-tight">{modalFeature.confidence || '98%'}</div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800/40 p-5 rounded-2xl border border-slate-200 dark:border-slate-700/50">
                    <div className="flex items-center space-x-2 text-slate-500 mb-2">
                      <ShieldAlert className="w-4 h-4" />
                      <span className="text-[10px] font-black uppercase tracking-widest">Severity</span>
                    </div>
                    <div className="text-2xl font-black tracking-tight" style={{ color: SEVERITY_COLORS[modalFeature.severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.Default }}>
                      {modalFeature.severity?.toUpperCase()}
                    </div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800/40 p-5 rounded-2xl border border-slate-200 dark:border-slate-700/50">
                    <div className="flex items-center space-x-2 text-slate-500 mb-2">
                      <Globe className="w-4 h-4" />
                      <span className="text-[10px] font-black uppercase tracking-widest">Source</span>
                    </div>
                    <div className="text-2xl font-black text-blue-500 dark:text-blue-400 tracking-tight">AI SIGHT</div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="font-black text-slate-700 dark:text-slate-100 flex items-center space-x-2 uppercase tracking-widest text-xs">
                    <Info className="w-4 h-4 text-blue-500" />
                    <span>Inference Context</span>
                  </h3>
                  <div className="bg-white dark:bg-slate-950/50 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 text-sm leading-relaxed font-medium">
                    {modalFeature.description || "In-depth analysis of textual mentions combined with visual variance mapping. This area shows markers indicative of the specified criticality level."}
                  </div>
                </div>
              </div>

              <div className="p-6 bg-slate-50/50 dark:bg-slate-800/30 border-t border-slate-200 dark:border-slate-800 flex justify-end space-x-3">
                <button 
                  onClick={() => setModalFeature(null)}
                  className="px-8 py-3 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-black uppercase tracking-widest transition-all border border-slate-300 dark:border-slate-700"
                >
                  Dismiss
                </button>
                <button 
                  className="px-8 py-3 text-white rounded-xl text-xs font-black uppercase tracking-widest shadow-lg transition-all border flex items-center space-x-2"
                  style={{ backgroundColor: SEVERITY_COLORS[modalFeature.severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.Default, borderColor: `${SEVERITY_COLORS[modalFeature.severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.Default}44` }}
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>Push to Database</span>
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className={`w-full h-full flex ${viewMode === 'split' ? 'flex-row' : ''}`}>
        <div className="flex-1 h-full relative">
          <MapContainer center={[20.5937, 78.9629]} zoom={5} zoomControl={false}>
            <TileLayer url={theme === 'dark' ? darkTiles : lightTiles} />
            {analysisResult && analysisResult.geospatialData && (
              <InteractiveGeoJson 
                key={`${analysisResult.taskId}-geo-themed`}
                data={analysisResult.geospatialData as any} 
                onSelect={setSelectedFeature}
                onOpenModal={setModalFeature}
              />
            )}
            <MapController result={analysisResult} />
            <ZoomControl position="bottomright" />
          </MapContainer>
        </div>

        {viewMode === 'split' && (
          <div className="flex-1 h-full relative border-l border-slate-200 dark:border-slate-800">
             <MapContainer center={[20.5937, 78.9629]} zoom={5} zoomControl={false}>
                <TileLayer url={theme === 'dark' ? lightTiles : darkTiles} />
                <MapController result={analysisResult} />
              </MapContainer>
          </div>
        )}
      </div>

      <MapLegend theme={theme} />

      <div className="absolute bottom-6 left-6 z-[1000] pointer-events-none">
        <div className="bg-white/90 dark:bg-slate-950/90 backdrop-blur-xl px-5 py-2.5 rounded-full border border-slate-200 dark:border-blue-500/30 flex items-center space-x-4 text-[10px] font-black uppercase tracking-[0.2em] shadow-2xl transition-colors">
          <MousePointer2 className="w-3.5 h-3.5 text-blue-500" />
          <span className="text-slate-700 dark:text-slate-200">Severity Mapping Core Active</span>
        </div>
      </div>
    </div>
  );
};