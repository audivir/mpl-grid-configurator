import { FigSize, Layout } from "../lib/layout";
import { cn } from "react-lib-tools";
import {
  Settings,
  RotateCcw,
  Download,
  ClipboardCopy,
  Check,
  Import,
  Redo2,
  Undo2,
} from "lucide-react";
import { SetStateAction, useState } from "react";
import ControlButton from "./ControlButton";
import { copyContentToClipboard, downloadContent } from "../lib/content";

interface SidebarProps {
  collapsed: boolean;
  layout: Layout;
  figsize: FigSize;
  figsizePreview: FigSize;
  setFigsizePreview: (v: SetStateAction<FigSize>) => void;
  commitFigsize: () => void;
  zoom: number;
  setZoom: (v: SetStateAction<number>) => void;
  showOverlay: boolean;
  setShowOverlay: (v: SetStateAction<boolean>) => void;
  handleReset: (l: Layout, fs: FigSize) => void;
  svgContent: string;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  layout,
  figsize,
  figsizePreview,
  setFigsizePreview,
  commitFigsize,
  zoom,
  setZoom,
  showOverlay,
  setShowOverlay,
  handleReset,
  svgContent,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
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
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onUndo}
            disabled={!canUndo}
            className={cn(
              "flex items-center justify-center gap-2 py-2 rounded border transition-all text-xs font-bold",
              canUndo
                ? "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"
                : "bg-slate-900/50 border-slate-800 text-slate-600 cursor-not-allowed opacity-50"
            )}
          >
            <Undo2 size={14} /> UNDO
          </button>
          <button
            onClick={onRedo}
            disabled={!canRedo}
            className={cn(
              "flex items-center justify-center gap-2 py-2 rounded border transition-all text-xs font-bold",
              canRedo
                ? "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"
                : "bg-slate-900/50 border-slate-800 text-slate-600 cursor-not-allowed opacity-50"
            )}
          >
            REDO <Redo2 size={14} />
          </button>
        </div>

        <div className="pt-4 border-t border-slate-700/50 flex justify-between items-center">
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
            <span className="text-blue-400">{figsizePreview.w}</span>
          </div>
          <input
            type="range"
            min="4"
            max="24"
            step="0.5"
            value={figsizePreview.w}
            onChange={(e) => {
              setFigsizePreview((prev) => ({ ...prev, w: +e.target.value }));
            }}
            onMouseUp={commitFigsize}
            onKeyUp={commitFigsize}
            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />

          <div className="flex justify-between text-xs text-slate-500 font-bold uppercase tracking-wider">
            <span>Height</span>
            <span className="text-blue-400">{figsizePreview.h}</span>
          </div>
          <input
            type="range"
            min="2"
            max="18"
            step="0.5"
            value={figsizePreview.h}
            onChange={(e) =>
              setFigsizePreview((prev) => ({ ...prev, h: +e.target.value }))
            }
            onMouseUp={commitFigsize}
            onKeyUp={commitFigsize}
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
                  handleReset(p.layout, p.figsize);
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
              window.confirm("Reset all progress?") &&
              handleReset("draw_empty", { w: 8, h: 4 })
            }
          />
        </div>
      </section>
    </aside>
  );
};

export default Sidebar;
