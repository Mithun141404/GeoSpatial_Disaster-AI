import React, { useState, useEffect } from 'react';
import { Sidebar, SidebarBody, SidebarLink } from './components/ui/sidebar';
import { MapViewer } from './components/MapViewer';
import { FileUpload } from './components/FileUpload';
import { AnalysisPanel } from './components/AnalysisPanel';
import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { AnalysisResult } from './types';
import { motion, AnimatePresence } from 'framer-motion';
import { Map, BarChart3, Settings, Trash2, Shield, Info, Home } from 'lucide-react';
import { LumaSpin } from './components/ui/luma-spin';

const App: React.FC = () => {
  const [view, setView] = useState<'landing' | 'portal'>('landing');
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [isProcessing, setIsProcessing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<'map' | 'analysis'>('map');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
  }, [theme]);

  const handleUploadComplete = (result: AnalysisResult) => {
    setAnalysisResult(result);
    setIsProcessing(false);
    setActiveTab('analysis');
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setActiveTab('map');
    setIsProcessing(false);
  };

  const links = [
    {
      label: "Geo Explorer",
      href: "#",
      icon: <Map className="w-5 h-5 flex-shrink-0" />,
      onClick: () => setActiveTab('map'),
      active: activeTab === 'map',
      disabled: !analysisResult
    },
    {
      label: "AI Reasoning",
      href: "#",
      icon: <BarChart3 className="w-5 h-5 flex-shrink-0" />,
      onClick: () => setActiveTab('analysis'),
      disabled: !analysisResult,
      active: activeTab === 'analysis'
    },
    {
      label: "Back to Home",
      href: "#",
      icon: <Home className="w-5 h-5 flex-shrink-0" />,
      onClick: () => setView('landing'),
    }
  ];

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-slate-50 dark:bg-slate-950 relative">
      <AnimatePresence mode="wait">
        {view === 'landing' ? (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="absolute inset-0 z-[100]"
          >
            <Hero onEnter={() => setView('portal')} />
          </motion.div>
        ) : (
          <motion.div
            key="portal"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col h-full w-full"
          >
            <Header theme={theme} onThemeToggle={() => setTheme(prev => prev === 'light' ? 'dark' : 'light')} />
            
            <main className="flex flex-1 overflow-hidden relative bg-transparent">
              <Sidebar open={sidebarOpen} setOpen={setSidebarOpen}>
                <SidebarBody className="justify-between gap-10 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
                  <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
                    <div className="flex items-center space-x-2 px-1 mb-8">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shrink-0">
                        <Shield className="text-white w-5 h-5" />
                      </div>
                      {sidebarOpen && (
                        <motion.span 
                          initial={{ opacity: 0 }} 
                          animate={{ opacity: 1 }} 
                          className="font-black text-xs uppercase tracking-widest text-slate-900 dark:text-white"
                        >
                          Intel Hub
                        </motion.span>
                      )}
                    </div>
                    
                    <div className="flex flex-col gap-2">
                      {links.map((link, idx) => (
                        <SidebarLink key={idx} link={link} active={(link as any).active} />
                      ))}

                      {analysisResult && (
                        <SidebarLink
                          link={{
                            label: "Clear All",
                            href: "#",
                            icon: <Trash2 className="w-5 h-5 flex-shrink-0" />,
                            onClick: handleReset
                          }}
                          className="text-red-500 hover:text-red-400 hover:bg-red-500/10"
                        />
                      )}
                    </div>
                  </div>

                  <div>
                    <SidebarLink
                      link={{
                        label: "System Settings",
                        href: "#",
                        icon: <Settings className="w-5 h-5 flex-shrink-0" />,
                      }}
                    />
                    {sidebarOpen && (
                      <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="mt-4 p-4 bg-slate-100 dark:bg-slate-800/50 rounded-2xl border border-slate-200 dark:border-slate-700"
                      >
                        <div className="flex items-center space-x-2 text-blue-500 mb-2">
                          <Info className="w-4 h-4" />
                          <span className="text-[10px] font-black uppercase tracking-wider">Credits</span>
                        </div>
                        <div className="w-full bg-slate-200 dark:bg-slate-700 h-1 rounded-full overflow-hidden mb-1">
                          <div className="bg-blue-500 h-full w-[65%]"></div>
                        </div>
                        <p className="text-[10px] text-slate-500 font-bold">650 / 1000 GPU Units</p>
                      </motion.div>
                    )}
                  </div>
                </SidebarBody>
              </Sidebar>
              
              <div className="flex-1 relative p-4 flex gap-4 overflow-hidden">
                <div className="flex-1 h-full relative overflow-hidden bg-white/50 dark:bg-slate-900/50 rounded-2xl border border-slate-200 dark:border-slate-800/50">
                  <AnimatePresence mode="wait">
                    {analysisResult ? (
                      activeTab === 'map' ? (
                        <motion.div 
                          key="map"
                          initial={{ opacity: 0, scale: 0.98 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.98 }}
                          className="w-full h-full"
                        >
                          <MapViewer analysisResult={analysisResult} theme={theme} />
                        </motion.div>
                      ) : (
                        <motion.div 
                          key="analysis"
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -20 }}
                          className="w-full h-full overflow-y-auto px-2 py-4"
                        >
                          <AnalysisPanel result={analysisResult} />
                        </motion.div>
                      )
                    ) : null}
                  </AnimatePresence>

                  {!analysisResult && !isProcessing && (
                    <motion.div 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="absolute inset-0 flex items-center justify-center bg-white/40 dark:bg-slate-950/40 backdrop-blur-md z-[50] rounded-2xl pointer-events-auto"
                    >
                      <FileUpload onStart={() => setIsProcessing(true)} onComplete={handleUploadComplete} />
                    </motion.div>
                  )}

                  {isProcessing && (
                    <motion.div 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 dark:bg-slate-950/80 backdrop-blur-xl z-[60] rounded-2xl space-y-10"
                    >
                      <LumaSpin />
                      
                      <div className="text-center">
                        <h3 className="text-2xl font-black text-slate-900 dark:text-white mb-3 tracking-tight">Synthesizing Geospatial Intelligence</h3>
                        <div className="flex flex-col space-y-1.5 text-slate-500 dark:text-slate-400 text-[10px] font-black uppercase tracking-[0.3em]">
                          <span className="flex items-center justify-center gap-2">
                             <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse"></div>
                             Mapping Segment Topology
                          </span>
                          <span className="flex items-center justify-center gap-2">
                             <div className="w-1 h-1 bg-indigo-500 rounded-full animate-pulse delay-75"></div>
                             Extracting Multi-Lingual NER
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>
              </div>
            </main>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default App;