import { SetStateAction, useEffect, useRef, useState } from "react";
import { cn } from "react-lib-tools";
import json5 from "json5";
import {
  Settings,
  RotateCcw,
  Download,
  ClipboardCopy,
  Check,
  Import,
  Redo2,
  Undo2,
  ChevronRight,
  ChevronLeft,
  Pin,
  PinOff,
  Copy,
} from "lucide-react";
import { toast } from "sonner";
import ControlButton from "./ControlButton";
import { LayoutActions } from "../lib/actions";
import { DEFAULT_FIGSIZE, DEFAULT_LAYOUT, STORAGE_KEYS } from "../lib/const";
import { copyContentToClipboard, downloadContent } from "../lib/content";
import { History } from "../lib/history";
import { ConfigSchema, FigureSize, Layout } from "../lib/layout";

interface SidebarProps {
  layout: Layout;
  figsize: FigureSize;
  figsizePreview: FigureSize;
  setFigsizePreview: (v: SetStateAction<FigureSize>) => void;
  zoom: number;
  setZoom: (v: SetStateAction<number>) => void;
  showOverlay: boolean;
  setShowOverlay: (v: SetStateAction<boolean>) => void;
  svgContent: string;
  setSvgContent: (v: SetStateAction<string>) => void;
  history: History;
  actions: LayoutActions;
}

const parseConfig = (raw: string) => {
  let json: any;
  try {
    json = JSON.parse(raw);
  } catch (err) {
    try {
      json = json5.parse(raw);
    } catch (err) {
      toast.error("Invalid JSON");
      return;
    }
    toast.warning("Input only parseable as JSON5, not JSON");
  }
  const config = ConfigSchema.safeParse(json);
  if (!config.success) {
    toast.error("JSON does not match expected schema");
    return;
  }
  return config.data;
};

const handleImport = (
  handleReset: (l: Layout, fs: FigureSize, msg?: string) => Promise<void>
) => {
  const raw = window.prompt("Paste Config JSON:");
  if (!raw) return;

  const config = parseConfig(raw);
  if (!config) return;

  handleReset(
    config.layout,
    config.figsize,
    "Configuration loaded successfully"
  );
};

const Sidebar: React.FC<SidebarProps> = ({
  layout,
  figsize,
  figsizePreview,
  setFigsizePreview,
  zoom,
  setZoom,
  showOverlay,
  setShowOverlay,
  svgContent,
  setSvgContent,
  history,
  actions,
}) => {
  const [isPinned, setIsPinned] = useState(
    localStorage.getItem(STORAGE_KEYS.SIDEBAR_PINNED) === "true"
  );

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.SIDEBAR_PINNED, isPinned.toString());
  }, [isPinned]);

  const [sidebarOpen, setSidebarOpen] = useState(isPinned);
  const closeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [configCopied, setConfigCopied] = useState(false);
  const [svgCopied, setSvgCopied] = useState(false);
  const [svgDownloaded, setSvgDownloaded] = useState(false);

  return (
    <>
      {!sidebarOpen && (
        <div
          onMouseEnter={() => {
            if (!sidebarOpen) {
              if (closeTimeoutRef.current)
                clearTimeout(closeTimeoutRef.current);
              setSidebarOpen(true);
              setIsPinned(false);
            }
          }}
          className="fixed left-0 top-0 bottom-0 w-2 z-50 cursor-e-resize"
        />
      )}
      <div
        className="relative h-full flex shrink-0"
        onClick={() => setIsPinned(true)}
        onMouseEnter={() => {
          if (closeTimeoutRef.current) {
            clearTimeout(closeTimeoutRef.current);
            closeTimeoutRef.current = null;
          }
        }}
        onMouseLeave={() => {
          if (!isPinned) {
            closeTimeoutRef.current = setTimeout(() => {
              setSidebarOpen(false);
            }, 400);
          }
        }}
      >
        {/* THE ACTUAL SIDEBAR */}
        <aside
          className={cn(
            "bg-[#1e293b] border-r border-slate-700 transition-all duration-300 ease-in-out h-full overflow-y-auto relative z-50",
            !sidebarOpen ? "w-0 p-0 opacity-0" : "w-[280px] p-6 opacity-100",
            !isPinned &&
              sidebarOpen &&
              "border-r-2 border-r-blue-500/50 shadow-[4px_0_24px_rgba(0,0,0,0.5)]"
          )}
        >
          <header className="flex items-center justify-between mb-8 pb-4 border-b border-slate-700">
            <div className="flex items-center gap-3">
              <Settings size={18} className="text-blue-400" />
              <h3 className="font-bold text-md tracking-widest uppercase text-slate-300">
                MPL GRID
              </h3>
            </div>

            <div className="flex items-center gap-1">
              {/* Pin Toggle Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsPinned(!isPinned);
                }}
                className={cn(
                  "p-1.5 rounded transition-all",
                  isPinned
                    ? "text-blue-400 bg-blue-500/10 hover:bg-blue-500/20"
                    : "text-slate-500 hover:text-slate-300 hover:bg-slate-700"
                )}
                title={
                  isPinned
                    ? "Unpin sidebar (auto-hide)"
                    : "Pin sidebar (stay open)"
                }
              >
                {isPinned ? (
                  <Pin size={16} fill="currentColor" />
                ) : (
                  <PinOff size={16} />
                )}
              </button>

              {/* Manual Collapse Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSidebarOpen(false);
                }}
                className="p-1.5 text-slate-500 hover:text-white hover:bg-slate-700 rounded transition-all"
                title="Collapse Sidebar"
              >
                <ChevronLeft size={20} />
              </button>
            </div>
          </header>

          <section className="space-y-6">
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={async () => {
                  const res = await history.undo();
                  if (res) {
                    setSvgContent(res.svg);
                    toast.success("Undo successful");
                  }
                }}
                disabled={!history.canUndo}
                className={cn(
                  "flex items-center justify-center gap-2 py-2 rounded border transition-all text-xs font-bold",
                  history.canUndo
                    ? "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"
                    : "bg-slate-900/50 border-slate-800 text-slate-600 cursor-not-allowed opacity-50"
                )}
              >
                <Undo2 size={14} /> UNDO
              </button>
              <button
                onClick={async () => {
                  const res = await history.redo();
                  if (res) {
                    setSvgContent(res.svg);
                    toast.success("Redo successful");
                  }
                }}
                disabled={!history.canRedo}
                className={cn(
                  "flex items-center justify-center gap-2 py-2 rounded border transition-all text-xs font-bold",
                  history.canRedo
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
                <span className="text-blue-400">{figsizePreview[0]}</span>
              </div>
              <input
                type="range"
                min="4"
                max="24"
                step="0.5"
                value={figsizePreview[0]}
                onChange={(e) => {
                  setFigsizePreview((prev) => [+e.target.value, prev[1]]);
                }}
                onMouseUp={() => actions.resize(figsizePreview)}
                onKeyUp={() => actions.resize(figsizePreview)}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />

              <div className="flex justify-between text-xs text-slate-500 font-bold uppercase tracking-wider">
                <span>Height</span>
                <span className="text-blue-400">{figsizePreview[1]}</span>
              </div>
              <input
                type="range"
                min="2"
                max="18"
                step="0.5"
                value={figsizePreview[1]}
                onChange={(e) =>
                  setFigsizePreview((prev) => [prev[0], +e.target.value])
                }
                onMouseUp={() => actions.resize(figsizePreview)}
                onKeyUp={() => actions.resize(figsizePreview)}
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
                onClick={() => handleImport(actions.reset)}
              />

              <ControlButton
                icon={svgCopied ? Check : Copy}
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
                  actions.reset(
                    DEFAULT_LAYOUT,
                    DEFAULT_FIGSIZE,
                    "Layout reset successfully"
                  )
                }
              />
            </div>
          </section>
        </aside>
        {!sidebarOpen && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setSidebarOpen(true);
              setIsPinned(true);
            }}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-[60] bg-[#1e293b] border border-l-0 border-slate-700 p-1.5 rounded-r-md text-slate-400 hover:text-white hover:bg-blue-600 transition-all shadow-xl"
          >
            <ChevronRight size={18} />
          </button>
        )}
      </div>
    </>
  );
};

export default Sidebar;
