import React from 'react';
import { Map, BarChart3, Settings, Database, Layers, Info, Trash2 } from 'lucide-react';

interface SidebarProps {
  activeTab: 'map' | 'analysis';
  setActiveTab: (tab: 'map' | 'analysis') => void;
  onReset: () => void;
  hasResult: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, onReset, hasResult }) => {
  const navItems = [
    { id: 'map', icon: Map, label: 'Geo Explorer' },
    { id: 'analysis', icon: BarChart3, label: 'AI Reasoning' },
  ];

  return (
    <aside className="w-20 lg:w-64 bg-slate-900 border-r border-slate-800 flex flex-col items-center lg:items-stretch py-6 space-y-8 z-20">
      <nav className="flex-1 space-y-2 px-3">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id as any)}
            disabled={item.id === 'analysis' && !hasResult}
            className={`w-full flex items-center space-x-3 px-3 py-3 rounded-xl transition-all ${
              activeTab === item.id 
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20' 
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            } ${item.id === 'analysis' && !hasResult ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            <span className="hidden lg:inline font-bold text-sm tracking-tight">{item.label}</span>
          </button>
        ))}
        
        <div className="h-px bg-slate-800 my-4 mx-3" />
        
        {hasResult && (
          <button 
            onClick={onReset}
            className="w-full flex items-center space-x-3 px-3 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-all border border-transparent hover:border-red-500/20"
          >
            <Trash2 className="w-5 h-5 flex-shrink-0" />
            <span className="hidden lg:inline font-bold text-sm tracking-tight">New Analysis</span>
          </button>
        )}

        <button className="w-full flex items-center space-x-3 px-3 py-3 rounded-xl text-slate-400 hover:bg-slate-800 hover:text-white transition-all">
          <Layers className="w-5 h-5 flex-shrink-0" />
          <span className="hidden lg:inline font-bold text-sm tracking-tight">Layers</span>
        </button>
      </nav>

      <div className="px-3 space-y-2">
        <button className="w-full flex items-center space-x-3 px-3 py-3 rounded-xl text-slate-400 hover:bg-slate-800 hover:text-white transition-all">
          <Settings className="w-5 h-5 flex-shrink-0" />
          <span className="hidden lg:inline font-bold text-sm tracking-tight">Settings</span>
        </button>
        <div className="p-4 bg-slate-800/50 rounded-2xl hidden lg:block border border-slate-700">
           <div className="flex items-center space-x-2 text-blue-400 mb-2">
             <Info className="w-4 h-4" />
             <span className="text-[10px] font-black uppercase tracking-wider">Credits</span>
           </div>
           <div className="w-full bg-slate-700 h-1 rounded-full overflow-hidden mb-1">
             <div className="bg-blue-500 h-full w-[65%]"></div>
           </div>
           <p className="text-[10px] text-slate-500 font-bold">650 / 1000 GPU Units</p>
        </div>
      </div>
    </aside>
  );
};