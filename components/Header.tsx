import React from 'react';
import { Shield, Bell } from 'lucide-react';
import { AnimatedThemeToggle } from './ui/animated-theme-toggle';

interface HeaderProps {
  theme: 'light' | 'dark';
  onThemeToggle: () => void;
}

export const Header: React.FC<HeaderProps> = ({ theme, onThemeToggle }) => {
  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 z-30 transition-colors">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
          <Shield className="text-white w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">Disaster<span className="text-blue-500">AI</span></h1>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-widest">Geospatial Intelligence</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden md:flex items-center bg-slate-100 dark:bg-slate-950 px-3 py-1 rounded-full border border-slate-200 dark:border-slate-800 space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">System Online</span>
        </div>
        
        <div className="flex items-center space-x-3 border-l border-slate-200 dark:border-slate-800 pl-4">
          <AnimatedThemeToggle theme={theme} onToggle={onThemeToggle} />
          
          <button className="text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors relative p-2">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-white dark:border-slate-900"></span>
          </button>
          
          <div className="flex items-center space-x-2 border-l border-slate-200 dark:border-slate-800 pl-4">
            <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden ring-2 ring-blue-500/20">
              <img src="https://picsum.photos/32/32" alt="Avatar" />
            </div>
            <span className="hidden sm:inline text-sm font-medium text-slate-700 dark:text-slate-300">Sr. Architect</span>
          </div>
        </div>
      </div>
    </header>
  );
};