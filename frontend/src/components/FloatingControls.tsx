import { SetStateAction } from "react";
import { Sidebar } from "lucide-react";

interface FloatingControlsProps {
  sidebarOpen: boolean;
  setSidebarOpen: (v: SetStateAction<boolean>) => void;
}

const FloatingControls: React.FC<FloatingControlsProps> = ({
  sidebarOpen,
  setSidebarOpen,
}) => {
  return (
    <div className="absolute inset-0 z-50 pointer-events-none p-6">
      <button
        className="pointer-events-auto p-2.5 bg-slate-800/80 backdrop-blur border border-slate-700 rounded-lg hover:bg-slate-700 text-white shadow-xl transition-all"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        <Sidebar size={18} />
      </button>
    </div>
  );
};

export default FloatingControls;
