import React from 'react';

export const LumaSpin = () => {
  return (
    <div className="relative w-[65px] aspect-square">
      <span className="absolute rounded-[50px] animate-loaderAnim shadow-[inset_0_0_0_3px] shadow-slate-800 dark:shadow-slate-100" />
      <span className="absolute rounded-[50px] animate-loaderAnim animation-delay shadow-[inset_0_0_0_3px] shadow-slate-800 dark:shadow-slate-100" />
    </div>
  );
};