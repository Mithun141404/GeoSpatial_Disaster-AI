import React from 'react';
import { AnalysisResult } from '../types';
import { motion } from 'framer-motion';
import { AlertTriangle, FileText, MapPin, CheckCircle2, Languages, ShieldCheck, Zap } from 'lucide-react';

interface AnalysisPanelProps {
  result: AnalysisResult | null;
}

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ result }) => {
  if (!result) return null;

  const isHighRisk = result.riskScore >= 75;

  return (
    <div className="space-y-6 pb-20">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Metrics & Actions */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="space-y-6 order-1 lg:order-1"
        >
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 text-center shadow-sm transition-colors">
            <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-8">Aggregate Risk Index</h3>
            
            {/* Centered Circle Container */}
            <div className="flex justify-center items-center">
              <div className="relative w-40 h-40">
                <svg className="w-full h-full transform -rotate-90">
                  <circle 
                    cx="80" 
                    cy="80" 
                    r="74" 
                    stroke="currentColor" 
                    strokeWidth="12" 
                    fill="transparent" 
                    className="text-slate-100 dark:text-slate-800" 
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="74"
                    stroke="currentColor"
                    strokeWidth="12"
                    fill="transparent"
                    strokeDasharray={465}
                    strokeDashoffset={465 - (465 * result.riskScore) / 100}
                    className={`transition-all duration-1000 ${isHighRisk ? 'text-red-500' : 'text-blue-500'}`}
                  />
                </svg>
                {/* Score Text Centering */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className={`text-4xl font-black tracking-tighter leading-none ${isHighRisk ? 'text-red-600 dark:text-red-500' : 'text-blue-600 dark:text-blue-500'}`}>
                    {result.riskScore}
                  </span>
                  <span className="text-[10px] font-black text-slate-500 uppercase mt-1">Score</span>
                </div>
              </div>
            </div>

            <p className={`mt-8 text-[10px] font-black uppercase tracking-[0.2em] ${isHighRisk ? 'text-red-500' : 'text-blue-500'}`}>
              {isHighRisk ? 'Critical Action Required' : 'Standard Monitoring'}
            </p>
          </div>

          <div className={`bg-gradient-to-br border rounded-2xl p-6 backdrop-blur-sm shadow-sm transition-all ${isHighRisk ? 'from-red-600/5 to-orange-600/5 border-red-200 dark:from-red-600/10 dark:to-orange-600/10 dark:border-red-500/30' : 'from-blue-600/5 to-indigo-600/5 border-blue-200 dark:from-blue-600/10 dark:to-indigo-600/10 dark:border-blue-500/30'}`}>
            <h4 className="font-black text-xs uppercase tracking-widest text-slate-900 dark:text-white mb-4 flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span>Recommended Actions</span>
            </h4>
            <ul className="space-y-4">
              {[
                "Initiate physical site inspection for anomaly zones",
                "Verify hash integrity of AgencyX log dump",
                "Deploy emergency patch to Geo Sentinel Node Alpha"
              ].map((action, i) => (
                <li key={i} className="flex items-start space-x-3 text-xs text-slate-600 dark:text-slate-300 font-bold leading-relaxed">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${isHighRisk ? 'bg-red-500/10 text-red-600' : 'bg-blue-500/10 text-blue-600'}`}>
                    <CheckCircle2 className="w-3 h-3" />
                  </div>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        </motion.div>

        {/* Right Column: Reasoning, Indicators & Entities */}
        <div className="lg:col-span-2 space-y-6 order-2 lg:order-2">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 shadow-sm transition-colors"
          >
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center space-x-4">
                <div className={`p-3 rounded-xl ${isHighRisk ? 'bg-red-500/10 text-red-600' : 'bg-blue-500/10 text-blue-600'}`}>
                   <FileText className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-xl font-black text-slate-900 dark:text-white tracking-tight">AI Multimodal Reasoning</h2>
                  <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest">Inference Report • {new Date(result.timestamp).toLocaleTimeString()}</p>
                </div>
              </div>
              <div className={`flex items-center space-x-2 px-4 py-1.5 rounded-full text-[10px] font-black border uppercase tracking-widest ${isHighRisk ? 'bg-red-50 text-red-600 border-red-200 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20' : 'bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20'}`}>
                {isHighRisk ? <AlertTriangle className="w-3 h-3" /> : <CheckCircle2 className="w-3 h-3" />}
                <span>{isHighRisk ? 'Critical Findings' : 'Verified Insight'}</span>
              </div>
            </div>
            
            <div className="bg-slate-50 dark:bg-slate-950/50 p-6 rounded-2xl border border-slate-200 dark:border-slate-800/50">
              <p className="text-slate-700 dark:text-slate-300 leading-relaxed text-sm font-medium italic">
                "{result.summary}"
              </p>
            </div>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors"
            >
              <div className="flex items-center space-x-3 mb-6">
                <Languages className="text-blue-500 w-5 h-5" />
                <h3 className="font-black text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400">Extracted Indicators</h3>
              </div>
              <div className="space-y-3">
                {result.indicators.map((ind, idx) => (
                  <div key={idx} className="flex items-start space-x-4 p-4 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 group hover:border-blue-500/30 transition-colors">
                    <Zap className="w-4 h-4 text-blue-500 mt-0.5" />
                    <span className="text-xs font-bold text-slate-700 dark:text-slate-200">{ind}</span>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors"
            >
              <div className="flex items-center space-x-3 mb-6">
                <MapPin className="text-emerald-500 w-5 h-5" />
                <h3 className="font-black text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400">NER Entity Extraction</h3>
              </div>
              <div className="flex flex-wrap gap-3">
                {result.entities.map((ent, idx) => (
                  <div key={idx} className="bg-slate-100 dark:bg-slate-800/50 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 group hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors">
                    <span className="text-[10px] font-black text-blue-600 dark:text-blue-400 uppercase tracking-tighter block mb-0.5">{ent.label}</span>
                    <span className="text-xs font-bold text-slate-800 dark:text-slate-200">{ent.text}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};