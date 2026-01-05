import { FigSize, Layout } from "../lib/layout";
import { cn } from "react-lib-tools";
import {
  Settings,
  RotateCcw,
  Download,
  ClipboardCopy,
  Check,
  Import,
} from "lucide-react";
import { SetStateAction, useState } from "react";
import ControlButton from "./ControlButton";
import { copyContentToClipboard, downloadContent } from "../lib/content";

interface SidebarProps {
  collapsed: boolean;
  layout: Layout;
  setLayout: (v: SetStateAction<Layout>) => void;
  figsize: FigSize;
  setFigsize: (v: SetStateAction<FigSize>) => void;
  zoom: number;
  setZoom: (v: SetStateAction<number>) => void;
  showOverlay: boolean;
  setShowOverlay: (v: SetStateAction<boolean>) => void;
  handleReset: () => void;
  svgContent: string;
}

const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  layout,
  setLayout,
  figsize,
  setFigsize,
  zoom,
  setZoom,
  showOverlay,
  setShowOverlay,
  handleReset,
  svgContent,
}) => {
  const [configCopied, setConfigCopied] = useState(false);
  const [svgCopied, setSvgCopied] = useState(false);
  const [svgDownloaded, setSvgDownloaded] = useState(false);

  return (
    <aside
      className={cn(
        "bg-[#1e293b] border-r border-slate-700 transition-all duration-300 ease-in-out shrink-0 overflow-y-auto",
        collapsed ? "w-0 p-0 opacity-0" : "w-[280px] p-6"
      )}
    >
      <header className="flex items-center gap-3 mb-8 pb-4 border-b border-slate-700">
        <Settings size={18} className="text-blue-400" />
        <h3 className="font-bold text-md tracking-widest uppercase text-slate-300">
          MPL GRID
        </h3>
      </header>

      <section className="space-y-6">
        <div className="flex justify-between items-center">
          <button
            onClick={() => setZoom((z) => Math.max(0.2, z - 0.1))}
            className="w-8 h-8 items-center justify-center hover:bg-slate-700 rounded text-lg"
          >
            -
          </button>
          <span className="text-sm font-mono w-10 text-center text-slate-400 font-bold">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.min(3, z + 0.1))}
            className="w-8 h-8 items-center justify-center hover:bg-slate-700 rounded text-lg"
          >
            +
          </button>
          <div className="w-px h-4 bg-slate-700 mx-1" />
          <button
            onClick={() => setZoom(1)}
            className="px-2 text-sm font-bold text-blue-400 hover:text-blue-300"
          >
            RESET
          </button>
        </div>

        <div className="pt-4 border-t border-slate-700/50 space-y-4">
          <div className="flex justify-between text-xs text-slate-500 font-bold uppercase tracking-wider">
            <span>Width</span>
            <span className="text-blue-400">{figsize.w}</span>
          </div>
          <input
            type="range"
            min="4"
            max="24"
            step="0.5"
            value={figsize.w}
            onChange={(e) =>
              setFigsize((prev) => ({ ...prev, w: +e.target.value }))
            }
            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />

          <div className="flex justify-between text-xs text-slate-500 font-bold uppercase tracking-wider">
            <span>Height</span>
            <span className="text-blue-400">{figsize.h}</span>
          </div>
          <input
            type="range"
            min="2"
            max="18"
            step="0.5"
            value={figsize.h}
            onChange={(e) =>
              setFigsize((prev) => ({ ...prev, h: +e.target.value }))
            }
            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>

        <div className="pt-4 space-y-2 border-t border-slate-700/50">
          <label className="flex items-center gap-3 py-2 px-1 cursor-pointer hover:text-white transition-colors">
            <input
              type="checkbox"
              checked={showOverlay}
              onChange={(e) => setShowOverlay(e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500"
            />
            <span className="text-sm font-medium">Show Overlay</span>
          </label>

          <ControlButton
            icon={configCopied ? Check : ClipboardCopy}
            label={configCopied ? "Copied!" : "Copy Config"}
            variant={configCopied ? "success" : "default"}
            onClick={() =>
              copyContentToClipboard(
                JSON.stringify({ layout, figsize }, null, 2),
                setConfigCopied
              )
            }
          />

          <ControlButton
            icon={Import}
            label="Import Config"
            onClick={() => {
              const raw = window.prompt("Paste Config JSON:");
              if (raw) {
                try {
                  const p = JSON.parse(raw);
                  setLayout(p.layout);
                  setFigsize(p.figsize);
                } catch {
                  alert("Invalid JSON");
                }
              }
            }}
          />

          <ControlButton
            icon={svgCopied ? Check : Download}
            label={svgCopied ? "Copied!" : "Copy SVG"}
            variant={svgCopied ? "success" : "default"}
            onClick={() => copyContentToClipboard(svgContent, setSvgCopied)}
          />

          <ControlButton
            icon={svgDownloaded ? Check : Download}
            label={svgDownloaded ? "Downloaded!" : "Download SVG"}
            variant={svgDownloaded ? "success" : "default"}
            onClick={() =>
              downloadContent(
                svgContent,
                "image/svg+xml",
                "plot.svg",
                setSvgDownloaded
              )
            }
          />

          <ControlButton
            icon={RotateCcw}
            label="Reset Layout"
            variant="danger"
            onClick={() =>
              window.confirm("Reset all progress?") && handleReset()
            }
          />
        </div>
      </section>
    </aside>
  );
};

export default Sidebar;
