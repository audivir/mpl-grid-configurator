import { useEffect, useRef, useState } from "react";
import { cn } from "react-lib-tools";
import { Group, Panel, Separator } from "react-resizable-panels";
import { debounce } from "lodash";
import {
  Columns,
  Rows,
  Trash2,
  Merge,
  RotateCcw,
  SwitchCamera,
} from "lucide-react";
import { LayoutActions } from "../lib/actions";
import { FigureSize, Layout, LPath } from "../lib/layout";

const DEBOUNCE_TIME = 100;

interface GridOverlayProps {
  layout: Layout;
  figsize: FigureSize;
  zoom: number;
  funcs: string[];
  actions: LayoutActions;
}

interface RecursiveGridProps {
  node: Layout;
  path: LPath;
  setIsButtonHovered: (v: boolean) => void;

}

interface DragButtonProps {
  icon: React.ElementType;
  setter: (pathId: string | null) => void;
}

/**
 * A button that can be dragged showing the full grandparent.
 * @param icon The icon to display on the button.
 * @param setter The function to call with the grandparent's id while dragging, and null when dragging ends.
 */
const DragButton: React.FC<DragButtonProps> = ({
  icon: Icon,
  setter,
}: DragButtonProps) => {
  return (
    <button
      draggable
      className="p-1 text-slate-400 hover:text-slate-600 cursor-grab active:cursor-grabbing"
      onDragStart={(e) => {
        const parent = (e.currentTarget as HTMLElement).parentElement!
          .parentElement!;
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
  layout,
  zoom,
  funcs,
  actions,
}) => {
  const [swapPathId, setSwapPathId] = useState<string | null>(null);
  const [mergePathId, setMergePathId] = useState<string | null>(null);

  const RecursiveGrid: React.FC<RecursiveGridProps> = ({ node, path, setIsButtonHovered }) => {
    const [isOver, setIsOver] = useState(false);
    const pathId = [0, ...path].join("-");

    const [isChildButtonHovered, setIsChildButtonHovered] = useState(false);
    const [isSeperatorActive, setIsSeperatorActive] = useState(false);
    const seperatorRef = useRef<HTMLDivElement>(null);

    const debouncedSetIsButtonHovered = debounce(setIsButtonHovered, DEBOUNCE_TIME);

    useEffect(() => {
      const el = seperatorRef.current;
      if (!el) return;
      const observer = new MutationObserver(debounce(() => {
          const state = el.getAttribute("data-separator");
          setIsSeperatorActive(state !== "inactive");
      }, DEBOUNCE_TIME));
      observer.observe(el, {
        attributes: true,
        attributeFilter: ["data-separator"],
      });
      return () => {
        observer.disconnect();
      };
    }, []);

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
            if (swapPathId) actions.swap(swapPathId, pathId);
            if (mergePathId) actions.merge(mergePathId, pathId);
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
              onClick={() => actions.split(path, "row")}
              style={{ transform: `scale(${1 / zoom})` }}
            >
              <Columns size={14} />
            </button>

            <div
              className="flex flex-wrap items-center justify-center gap-1 p-1 bg-white/95 border border-slate-200 rounded shadow-sm pointer-events-auto transform transition-transform group-hover:scale-105"
              id={pathId}
              style={{ transform: `scale(${1 / zoom})` }}
            >
              <select
                className="text-xs font-bold text-slate-700 bg-transparent border-none focus:ring-0 cursor-pointer outline-none px-1"
                value={node}
                onChange={(e) => actions.replace(path, e.target.value)}
              >
                {funcs.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
              {path.length > 0 && (
                <div className="flex items-center gap-1">
                  <DragButton
                    icon={SwitchCamera}
                    setter={(pathId) => {
                      setMergePathId(null); // assure no merge
                      setSwapPathId(pathId);
                    }}
                  />
                  <DragButton
                    icon={Merge}
                    setter={(pathId) => {
                      setSwapPathId(null); // assure no swap
                      setMergePathId(pathId);
                    }}
                  />
                  <button
                    className="p-1 text-blue-400 hover:text-blue-600"
                    onClick={() => actions.rotate(path.slice(0, -1))}
                    onMouseEnter={() => {debouncedSetIsButtonHovered(true)}}
                    onMouseLeave={() => {debouncedSetIsButtonHovered(false)}}
                  >
                    <RotateCcw size={14} />
                  </button>
                  <button
                    className="p-1 text-red-400 hover:text-red-600"
                    onClick={() => actions.delete(path)}
                    onMouseEnter={() => {debouncedSetIsButtonHovered(true)}}
                    onMouseLeave={() => {debouncedSetIsButtonHovered(false)}}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              )}
            </div>

            <button
              title="Split Vertical"
              className="absolute bottom-2 left-2 p-1.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-500 hover:bg-blue-500 hover:text-white origin-bottom-left transition-all pointer-events-auto opacity-0 group-hover:opacity-100"
              onClick={() => actions.split(path, "column")}
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
        className={cn(
          "w-full h-full",
          (isSeperatorActive || isChildButtonHovered) && "bg-blue-500/20"
        )}
        onLayoutChange={actions.restructure}
      >
        <Panel defaultSize={node.ratios[0]} id={pathId + "-0"}>
          <RecursiveGrid
            node={node.children[0]}
            path={[...path, 0]}
            setIsButtonHovered={setIsChildButtonHovered}
          />
        </Panel>
        <Separator
          className={cn(
            "bg-slate-200 hover:bg-blue-400 transition-colors",
            (isSeperatorActive || isChildButtonHovered) && "bg-blue-400",
            node.orient === "row" ? "w-1" : "h-1"
          )}
          elementRef={seperatorRef}
        />
        <Panel defaultSize={node.ratios[1]} id={pathId + "-1"}>
          <RecursiveGrid
            node={node.children[1]}
            path={[...path, 1]}
            setIsButtonHovered={setIsChildButtonHovered}
          />
        </Panel>
      </Group>
    );
  };

  return <RecursiveGrid node={layout} path={[]} setIsButtonHovered={() => {}}/>;
};

export default GridOverlay;
