import { useState, SetStateAction } from "react";
import { cn } from "react-lib-tools";
import { FigSize, Layout } from "../lib/layout";
import { Columns, Rows, Grip, Trash2, Merge } from "lucide-react";
import { Group, Panel, Separator } from "react-resizable-panels";
import gridCallbacks from "../lib/callbacks";

interface GridOverlayProps {
  setPresent: (l: Layout, fs: FigSize) => void;
  layout: Layout;
  figsize: FigSize;
  zoom: number;
  funcs: string[];
  resizeDebounce: number;
  mergeCallback: (p_a: string, p_b: string) => void;
}

interface RecursiveGridProps {
  node: Layout;
  path: number[];
}

interface DragButtonProps {
  icon: React.ElementType;
  setter: (pathId: string | null) => void;
}
const DragButton: React.FC<DragButtonProps> = ({
  icon: Icon,
  setter,
}: DragButtonProps) => {
  return (
    <button
      draggable
      className="p-1 text-slate-400 hover:text-slate-600 cursor-grab active:cursor-grabbing"
      onDragStart={(e) => {
        const parent = (e.currentTarget as HTMLElement).parentElement!;
        const pathId = parent.id;
        e.dataTransfer.setDragImage(parent, 20, 20);
        setter(pathId);
      }}
      onDragEnd={() => setter(null)}
    >
      <Icon size={14} />
    </button>
  );
};

const GridOverlay: React.FC<GridOverlayProps> = ({
  setPresent,
  layout,
  figsize,
  zoom,
  funcs,
  resizeDebounce,
  mergeCallback,
}) => {
  const [swapPathId, setSwapPathId] = useState<string | null>(null);
  const [mergePathId, setMergePathId] = useState<string | null>(null);

  const setLayout = (next: SetStateAction<Layout>) => {
    const value = typeof next === "function" ? next(layout) : next;
    setPresent(value, figsize);
  };

  const { handleSwap, handleSplit, handleLeaf, handleDelete, handleResize } =
    gridCallbacks({ layout, setLayout, resizeDebounce });

  const RecursiveGrid: React.FC<RecursiveGridProps> = ({ node, path }) => {
    const [isOver, setIsOver] = useState(false);
    const pathId = [0, ...path].join("-");

    if (typeof node === "string") {
      return (
        <div
          id={pathId}
          onDragOver={(e) => {
            e.preventDefault();
            setIsOver(true);
          }}
          onDragLeave={() => setIsOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsOver(false);
            // If the dragged object set the swapPathId, swap them.
            if (swapPathId && mergePathId)
              throw new Error("Cannot swap and merge at the same time");
            if (swapPathId) handleSwap(swapPathId, pathId);
            if (mergePathId) mergeCallback(mergePathId, pathId);
          }}
          className={cn(
            "relative w-full h-full border border-blue-500/10 transition-all group pointer-events-auto",
            isOver && "bg-blue-500/20 border-blue-500 border-2 z-20"
          )}
        >
          {/* Node Controls */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <button
              title="Split Horizontal"
              className="absolute top-2 right-2 p-1.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-500 hover:bg-blue-500 hover:text-white origin-top-right transition-all pointer-events-auto opacity-0 group-hover:opacity-100"
              onClick={() => handleSplit(path, "row")}
              style={{ transform: `scale(${1 / zoom})` }}
            >
              <Columns size={14} />
            </button>

            <div
              className="flex items-center gap-1 p-1 bg-white/95 border border-slate-200 rounded shadow-sm pointer-events-auto transform transition-transform group-hover:scale-105"
              id={pathId}
              style={{ transform: `scale(${1 / zoom})` }}
            >
              {path.length > 0 && (
                <DragButton
                  icon={Grip}
                  setter={(pathId) => {
                    setMergePathId(null); // assure no merge
                    setSwapPathId(pathId);
                  }}
                />
              )}
              <select
                className="text-[11px] font-bold text-slate-700 bg-transparent border-none focus:ring-0 cursor-pointer outline-none px-1"
                value={node}
                onChange={(e) => handleLeaf(path, e.target.value)}
              >
                {funcs.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
              {path.length > 0 && (
                <DragButton
                  icon={Merge}
                  setter={(pathId) => {
                    setSwapPathId(null); // assure no swap
                    setMergePathId(pathId);
                  }}
                />
              )}
              {path.length > 0 && (
                <button
                  className="p-1 text-red-400 hover:text-red-600"
                  onClick={() => handleDelete(path)}
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>

            <button
              title="Split Vertical"
              className="absolute bottom-2 left-2 p-1.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-500 hover:bg-blue-500 hover:text-white origin-bottom-left transition-all pointer-events-auto opacity-0 group-hover:opacity-100"
              onClick={() => handleSplit(path, "column")}
              style={{ transform: `scale(${1 / zoom})` }}
            >
              <Rows size={14} />
            </button>
          </div>
        </div>
      );
    }
    return (
      <Group
        orientation={node.orient === "row" ? "horizontal" : "vertical"}
        className="w-full h-full"
        onLayoutChange={handleResize}
      >
        <Panel defaultSize={node.ratios[0]} id={pathId + "-0"}>
          <RecursiveGrid node={node.children[0]} path={[...path, 0]} />
        </Panel>
        <Separator
          className={cn(
            "bg-slate-200 hover:bg-blue-400 transition-colors",
            node.orient === "row" ? "w-1" : "h-1"
          )}
        />
        <Panel defaultSize={node.ratios[1]} id={pathId + "-1"}>
          <RecursiveGrid node={node.children[1]} path={[...path, 1]} />
        </Panel>
      </Group>
    );
  };

  return <RecursiveGrid node={layout} path={[]} />;
};

export default GridOverlay;
