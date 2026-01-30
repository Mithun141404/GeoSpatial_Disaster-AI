
import React from 'react';
import { motion, Variants } from 'framer-motion';
import { Shield, Cpu, Globe, Database, ArrowRight, Scan, MessageSquareQuote } from 'lucide-react';
import ShaderBackground from './ui/shader-background';

interface HeroProps {
  onEnter: () => void;
}

export const Hero: React.FC<HeroProps> = ({ onEnter }) => {
  // Added Variants type to containerVariants for better type safety
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15, delayChildren: 0.3 }
    }
  };

  // Fixed itemVariants type error by using the Variants type and casting the easing array to an explicit 4-number tuple
  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 30 },
    visible: { 
      opacity: 1, 
      y: 0, 
      transition: { 
        duration: 0.8, 
        ease: [0.16, 1, 0.3, 1] as [number, number, number, number]
      } 
    }
  };

  const features = [
    {
      icon: <Scan className="w-5 h-5 text-blue-400" />,
      title: "SamGeo Segmentation",
      desc: "Precise geospatial masking of disaster-affected regions using Segment Anything."
    },
    {
      icon: <MessageSquareQuote className="w-5 h-5 text-purple-400" />,
      title: "LLaVA Reasoning",
      desc: "Vision-language models providing deep contextual reasoning over site imagery."
    },
    {
      icon: <Cpu className="w-5 h-5 text-emerald-400" />,
      title: "PaddleOCR Engine",
      desc: "Multi-lingual extraction of critical risk indicators from technical audit logs."
    },
    {
      icon: <Globe className="w-5 h-5 text-orange-400" />,
      title: "PostGIS Pipeline",
      desc: "Seamless conversion of AI inferences into actionable GeoJSON polygons."
    }
  ];

  return (
    <div className="relative w-full h-screen flex flex-col items-center justify-center overflow-hidden bg-slate-950">
      {/* Immersive Shader Background */}
      <ShaderBackground />
      
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 container mx-auto px-6 text-center max-w-5xl"
      >
        <motion.div variants={itemVariants} className="flex justify-center mb-8">
          <div className="p-4 bg-blue-600/20 rounded-3xl border border-blue-500/30 backdrop-blur-xl shadow-2xl shadow-blue-500/10">
            <Shield className="w-12 h-12 text-blue-500" />
          </div>
        </motion.div>

        <motion.h1 
          variants={itemVariants}
          className="text-6xl md:text-8xl font-black text-white tracking-tighter mb-6 italic"
        >
          DISASTER<span className="text-blue-600">AI</span>
        </motion.h1>

        <motion.p 
          variants={itemVariants}
          className="text-xl md:text-2xl text-slate-400 font-medium max-w-3xl mx-auto mb-12 leading-relaxed"
        >
          A multimodal geospatial intelligence system for rapid disaster assessment and technical authenticity auditing. 
          <span className="text-slate-200"> Synthesizing vision, text, and spatial data into actionable insight.</span>
        </motion.p>

        <motion.div variants={itemVariants} className="flex flex-wrap justify-center gap-4 mb-16">
          <button 
            onClick={onEnter}
            className="group relative px-10 py-5 bg-blue-600 hover:bg-blue-500 text-white font-black rounded-2xl transition-all shadow-2xl shadow-blue-600/30 flex items-center space-x-3 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
            <span className="uppercase tracking-widest text-sm">Launch Intelligence Portal</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
          
          <button className="px-10 py-5 bg-slate-900 hover:bg-slate-800 text-slate-300 font-black rounded-2xl transition-all border border-slate-800 flex items-center space-x-3">
             <Database className="w-5 h-5" />
             <span className="uppercase tracking-widest text-sm">Documentation</span>
          </button>
        </motion.div>

        <motion.div 
          variants={itemVariants}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 text-left"
        >
          {features.map((f, i) => (
            <div key={i} className="p-6 bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-[2rem] hover:border-slate-700 transition-colors group">
              <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                {f.icon}
              </div>
              <h3 className="text-white font-black text-sm uppercase tracking-wider mb-2">{f.title}</h3>
              <p className="text-slate-500 text-xs font-medium leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </motion.div>
      </motion.div>

      {/* Decorative gradient overlay */}
      <div className="absolute bottom-0 left-0 w-full h-64 bg-gradient-to-t from-slate-950 to-transparent pointer-events-none z-0"></div>
    </div>
  );
};
