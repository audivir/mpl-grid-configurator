import React from "react";
import { DEFAULT_DPI } from "../lib/const";
import { FigSize } from "../lib/layout";

interface PreviewOverlayProps {
  figsize: FigSize;
}

const PreviewOverlay: React.FC<PreviewOverlayProps> = ({ figsize }) => {
  const width = `${figsize.w * DEFAULT_DPI}px`;
  const height = `${figsize.h * DEFAULT_DPI}px`;

  return (
    <div
      className="absolute top-0 left-0 z-20 pointer-events-none transition-all duration-75 ease-out will-change-transform origin-top-left border-2 border-dashed border-blue-500/80 bg-blue-500/5"
      style={{ width, height }}
    >
      <div className="absolute bottom-2 right-2 text-xs font-bold text-blue-500 bg-white/80 px-1 rounded">
        {figsize.w} x {figsize.h}
      </div>
    </div>
  );
};

export default PreviewOverlay;
