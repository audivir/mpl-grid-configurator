import { SetStateAction } from "react";
import { Sidebar } from "lucide-react";

interface FloatingControlsProps {
  sidebarOpen: boolean;
  setSidebarOpen: (v: SetStateAction<boolean>) => void;
  zoom: number;
  setZoom: (v: SetStateAction<number>) => void;
}

const FloatingControls: React.FC<FloatingControlsProps> = ({
  sidebarOpen,
  setSidebarOpen,
  zoom,
  setZoom,
}) => {
  return (
    <div className="absolute inset-0 z-50 pointer-events-none p-6">
      <button
        className="pointer-events-auto p-2.5 bg-slate-800/80 backdrop-blur border border-slate-700 rounded-lg hover:bg-slate-700 text-white shadow-xl transition-all"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        <Sidebar size={18} />
      </button>

      <div className="pointer-events-auto absolute right-6 top-6 flex items-center gap-2 p-1.5 bg-slate-800/80 backdrop-blur border border-slate-700 rounded-lg shadow-xl">
        <button
          onClick={() => setZoom((z) => Math.max(0.2, z - 0.1))}
          className="w-8 h-8 flex items-center justify-center hover:bg-slate-700 rounded text-lg"
        >
          -
        </button>
        <span className="text-[10px] font-mono w-10 text-center text-slate-400 font-bold">
          {Math.round(zoom * 100)}%
        </span>
        <button
          onClick={() => setZoom((z) => Math.min(3, z + 0.1))}
          className="w-8 h-8 flex items-center justify-center hover:bg-slate-700 rounded text-lg"
        >
          +
        </button>
        <div className="w-px h-4 bg-slate-700 mx-1" />
        <button
          onClick={() => setZoom(1)}
          className="px-2 text-[10px] font-bold text-blue-400 hover:text-blue-300"
        >
          RESET
        </button>
      </div>
    </div>
  );
};

export default FloatingControls;
