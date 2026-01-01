import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Panel, Group, Separator, Layout as ResizedLayout } from 'react-resizable-panels';
import { debounce, cloneDeep } from 'lodash';
import {
    Settings,
    Sidebar as SidebarIcon,
    Columns,
    Rows,
    Trash2,
    RotateCcw,
    ClipboardCopy,
    Check,
    Import,
    Download,
    Grip,
} from 'lucide-react';
import { cn } from 'react-lib-tools';

const API_BASE = "http://localhost:8765";
const DEFAULT_DPI = 96;
const STORAGE_KEYS = {
    LAYOUT: 'plot-layout-v1',
    FIGSIZE: 'plot-figsize-v1'
} as const;

type Orientation = 'row' | 'column';
type LayoutNode = {
    orient: Orientation;
    children: [Layout, Layout];
    ratios: [number, number];
};
type Layout = string | LayoutNode;

interface FigSize {
    w: number;
    h: number;
}

interface ControlButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    icon: React.ElementType;
    label: string;
    variant?: 'default' | 'danger' | 'success';
}

const ControlButton = ({ icon: Icon, label, variant = 'default', className, ...props }: ControlButtonProps) => {
    const variants = {
        default: "text-slate-400 hover:text-blue-400",
        danger: "text-slate-400 hover:text-red-400",
        success: "text-green-400"
    };

    return (
        <button
            className={cn(
                "flex items-center gap-3 w-full py-2 px-1 transition-colors text-sm font-medium outline-none",
                variants[variant],
                className
            )}
            {...props}
        >
            <Icon size={16} />
            {label}
        </button>
    );
};

const App: React.FC = () => {
    const [availableFuncs, setAvailableFuncs] = useState<string[]>([]);
    const [svgContent, setSvgContent] = useState<string>("");
    const [showOverlay, setShowOverlay] = useState(true);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [configCopied, setConfigCopied] = useState(false);
    const [svgCopied, setSvgCopied] = useState(false);
    const [zoom, setZoom] = useState(1);
    const [draggedPath, setDraggedPath] = useState<string | null>(null);

    const [figsize, setFigsize] = useState<FigSize>(() => {
        const saved = localStorage.getItem(STORAGE_KEYS.FIGSIZE);
        return saved ? JSON.parse(saved) : { w: 8, h: 4 };
    });

    const [layout, setLayout] = useState<Layout>(() => {
        const saved = localStorage.getItem(STORAGE_KEYS.LAYOUT);
        return saved ? JSON.parse(saved) : "draw_empty";
    });

    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.FIGSIZE, JSON.stringify(figsize));
    }, [figsize]);

    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.LAYOUT, JSON.stringify(layout));
    }, [layout]);

    const renderLayout = useMemo(() => debounce(async (l: Layout, fs: FigSize) => {
        try {
            const response = await fetch(`${API_BASE}/render`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ layout: l, figsize: [fs.w, fs.h] })
            });
            if (response.ok) {
                const data = await response.json();
                setSvgContent(data.svg);
            }
        } catch (e) {
            console.error("Rendering failed:", e);
        }
    }, 400), []);

    useEffect(() => {
        fetch(`${API_BASE}/functions`)
            .then(r => r.json())
            .then(data => {
                setAvailableFuncs(data);
            })
            .catch(err => console.error("Could not fetch functions:", err));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        renderLayout(layout, figsize);
    }, [layout, figsize, renderLayout]);

    const updateAtSubPath = useCallback((path: number[], updater: (node: Layout) => Layout) => {
        setLayout(prev => {
            const next = cloneDeep(prev);
            if (path.length === 0) return updater(next);

            let target = next as LayoutNode;
            for (let i = 0; i < path.length - 1; i++) {
                target = target.children[path[i]] as LayoutNode;
            }
            const lastIdx = path[path.length - 1];
            target.children[lastIdx] = updater(target.children[lastIdx]);
            return next;
        });
    }, []);

    const haveRatiosChanged = (oldRatios: [number, number], newRatios: [number, number]) => {
        const EPSILON = 0.01;
        return oldRatios.some((val, idx) => Math.abs(val - newRatios[idx]) > EPSILON);
    };

    const instantHandleRatioChange = (path: number[], newRatios: [number, number], force: boolean = false) => {
        setLayout(prev => {
            const next = cloneDeep(prev);

            // Navigate to the target node
            let target = next as LayoutNode;
            if (path.length === 0) {
                // Root node check
                if (typeof next === 'string' || (!haveRatiosChanged(next.ratios, newRatios) && !force)) return prev;
                next.ratios = newRatios;
            } else {
                for (let i = 0; i < path.length - 1; i++) {
                    target = target.children[path[i]] as LayoutNode;
                }
                const lastIdx = path[path.length - 1];
                const targetNode = target.children[lastIdx] as LayoutNode;

                // GUARD: If ratios haven't really changed, return previous state object
                // returning 'prev' (the same reference) prevents a React re-render
                if (typeof targetNode === "string" || (!haveRatiosChanged(targetNode.ratios, newRatios) && !force)) {
                    return prev;
                }

                targetNode.ratios = newRatios;
            }
            return next;
        });
    };

    const debouncedHandleRatioChange = useMemo(
        () =>
            debounce((path: number[], newRatios: [number, number]) => {
                instantHandleRatioChange(path, newRatios);
            }, 100),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        []
    );
    const handleRatioChange = (resizedLayout: ResizedLayout) => {
        const path = Object.keys(resizedLayout)[0]
            .split("-")
            .slice(1, -1)
            .map(Number);
        const [left_up, right_down] = Object.values(resizedLayout);

        debouncedHandleRatioChange(path, [left_up, right_down])
    };

    const handleSplit = (path: number[], orient: Orientation) => {
        updateAtSubPath(path, (currentLeaf) => ({
            orient,
            ratios: [50, 50],
            children: [currentLeaf, currentLeaf]
        }));
        renderLayout(layout, figsize); // without debounce
    };

    const handleDelete = (path: number[]) => {
        if (path.length === 0) return;
        const parentPath = path.slice(0, -1);
        const indexToDelete = path[path.length - 1];
        const siblingIndex = indexToDelete === 0 ? 1 : 0;

        setLayout(prev => {
            const next = cloneDeep(prev);
            if (parentPath.length === 0) return (next as LayoutNode).children[siblingIndex];
            let target = next as LayoutNode;
            for (let i = 0; i < parentPath.length - 1; i++) {
                target = target.children[parentPath[i]] as LayoutNode;
            }
            const lastParentIdx = parentPath[parentPath.length - 1];
            const siblingNode = (target.children[lastParentIdx] as LayoutNode).children[siblingIndex];
            target.children[lastParentIdx] = siblingNode;
            return next;
        });
    };

    const handleSwap = (pathIdA: string, pathIdB: string) => {
        if (pathIdA === pathIdB) return;
        const pathA = pathIdA.split("-").slice(1).map(Number);
        const pathB = pathIdB.split("-").slice(1).map(Number);

        setLayout(prev => {
            const next = cloneDeep(prev);

            const getAt = (root: Layout, p: number[]) => {
                let curr = root;
                for (let i = 0; i < p.length; i++) curr = (curr as LayoutNode).children[p[i]];
                return curr as string;
            };

            const setAt = (root: Layout, p: number[], val: string) => {
                if (p.length === 0) return;
                let curr = root as LayoutNode;
                for (let i = 0; i < p.length - 1; i++) curr = curr.children[p[i]] as LayoutNode;
                curr.children[p[p.length - 1]] = val;
            };

            const valA = cloneDeep(getAt(next, pathA));
            const valB = cloneDeep(getAt(next, pathB));

            setAt(next, pathA, valB);
            setAt(next, pathB, valA);
            return next;
        });
    };

    const copyToClipboard = async (text: string, setter: (v: boolean) => void) => {
        await navigator.clipboard.writeText(text);
        setter(true);
        setTimeout(() => setter(false), 2000);
    };

    const downloadSvg = () => {
        const blob = new Blob([svgContent], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'plot.svg';
        a.click();
        URL.revokeObjectURL(url);
    };

    const RecursiveGrid = ({ node, path }: { node: Layout; path: number[] }) => {
        const [isOver, setIsOver] = useState(false);
        const pathId = [0, ...path].join("-");

        if (typeof node === "string") {
            return (
                <div
                    id={pathId}
                    onDragOver={(e) => { e.preventDefault(); setIsOver(true); }}
                    onDragLeave={() => setIsOver(false)}
                    onDrop={(e) => {
                        e.preventDefault();
                        setIsOver(false);
                        if (draggedPath) handleSwap(draggedPath, pathId);
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
                                <button
                                    draggable
                                    className="p-1 text-slate-400 hover:text-slate-600 cursor-grab active:cursor-grabbing"
                                    onDragStart={(e) => {
                                        const parent = (e.currentTarget as HTMLElement).parentElement!;
                                        const pathId = parent.id;
                                        e.dataTransfer.setDragImage(parent, 20, 20);
                                        setDraggedPath(pathId);
                                    }}
                                    onDragEnd={() => setDraggedPath(null)}
                                >
                                    <Grip size={12} />
                                </button>
                            )}
                            <select
                                className="text-[11px] font-bold text-slate-700 bg-transparent border-none focus:ring-0 cursor-pointer outline-none px-1"
                                value={node}
                                onChange={e => updateAtSubPath(path, () => e.target.value)}
                            >
                                {availableFuncs.map(f => <option key={f} value={f}>{f}</option>)}
                            </select>
                            {path.length > 0 && (
                                <button className="p-1 text-red-400 hover:text-red-600" onClick={() => handleDelete(path)}>
                                    <Trash2 size={12} />
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
                onLayoutChange={handleRatioChange}
            >
                <Panel defaultSize={node.ratios[0]} id={pathId + "-0"}>
                    <RecursiveGrid node={node.children[0]} path={[...path, 0]} />
                </Panel>
                <Separator className={cn(
                    "bg-slate-200 hover:bg-blue-400 transition-colors",
                    node.orient === "row" ? "w-1" : "h-1"
                )}
                    onDoubleClick={() => {
                        instantHandleRatioChange(path, [50, 50], true); // also on minimal changed ratios
                        renderLayout(layout, figsize); // without debounce
                    }}
                />
                <Panel defaultSize={node.ratios[1]} id={pathId + "-1"}>
                    <RecursiveGrid node={node.children[1]} path={[...path, 1]} />
                </Panel>
            </Group>
        );
    };


    return (
        <div className="flex w-screen h-screen bg-[#0f172a] text-[#f1f5f9] font-sans overflow-hidden select-none">
            {/* Sidebar */}
            <aside className={cn(
                "bg-[#1e293b] border-r border-slate-700 transition-all duration-300 ease-in-out shrink-0 overflow-y-auto",
                sidebarOpen ? "w-[280px] p-6" : "w-0 p-0 opacity-0"
            )}>
                <header className="flex items-center gap-3 mb-8 pb-4 border-b border-slate-700">
                    <Settings size={18} className="text-blue-400" />
                    <h3 className="font-bold text-xs tracking-widest uppercase text-slate-300">MPL GRID</h3>
                </header>

                <section className="space-y-6">
                    <div className="space-y-4">
                        <div className="flex justify-between text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                            <span>Width</span>
                            <span className="text-blue-400">{figsize.w}</span>
                        </div>
                        <input
                            type="range" min="4" max="24" step="0.5"
                            value={figsize.w}
                            onChange={e => setFigsize(prev => ({ ...prev, w: +e.target.value }))}
                            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                        />

                        <div className="flex justify-between text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                            <span>Height</span>
                            <span className="text-blue-400">{figsize.h}</span>
                        </div>
                        <input
                            type="range" min="2" max="18" step="0.5"
                            value={figsize.h}
                            onChange={e => setFigsize(prev => ({ ...prev, h: +e.target.value }))}
                            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                        />
                    </div>

                    <div className="pt-4 space-y-2 border-t border-slate-700/50">
                        <label className="flex items-center gap-3 py-2 px-1 cursor-pointer hover:text-white transition-colors">
                            <input
                                type="checkbox" checked={showOverlay}
                                onChange={e => setShowOverlay(e.target.checked)}
                                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500"
                            />
                            <span className="text-sm font-medium">Show Overlay</span>
                        </label>

                        <ControlButton
                            icon={configCopied ? Check : ClipboardCopy}
                            label={configCopied ? "Copied!" : "Copy Config"}
                            variant={configCopied ? "success" : "default"}
                            onClick={() => copyToClipboard(JSON.stringify({ layout, figsize }, null, 2), setConfigCopied)}
                        />

                        <ControlButton
                            icon={Import}
                            label="Import Config"
                            onClick={() => {
                                const raw = window.prompt("Paste Config JSON:");
                                if (raw) {
                                    try {
                                        const p = JSON.parse(raw);
                                        setLayout(p.layout); setFigsize(p.figsize);
                                    } catch { alert("Invalid JSON"); }
                                }
                            }}
                        />

                        <ControlButton
                            icon={svgCopied ? Check : Download}
                            label={svgCopied ? "Copied!" : "Copy SVG"}
                            variant={svgCopied ? "success" : "default"}
                            onClick={() => copyToClipboard(svgContent, setSvgCopied)}
                        />

                        <ControlButton icon={Download} label="Download SVG" onClick={downloadSvg} />

                        <ControlButton
                            icon={RotateCcw}
                            label="Reset Layout"
                            variant="danger"
                            onClick={() => {
                                if (!window.confirm("Reset all progress?")) return;
                                setFigsize({ w: 8, h: 4 });
                                setLayout("draw_empty");
                            }}
                        />
                    </div>
                </section>
            </aside>

            {/* Workspace Viewport */}
            <main className="relative flex-1 bg-[#0f172a] overflow-hidden">
                {/* Floating Controls */}
                {showOverlay && <div className="absolute inset-0 z-50 pointer-events-none p-6">
                    <button
                        className="pointer-events-auto p-2.5 bg-slate-800/80 backdrop-blur border border-slate-700 rounded-lg hover:bg-slate-700 text-white shadow-xl transition-all"
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                    >
                        <SidebarIcon size={18} />
                    </button>

                    <div className="pointer-events-auto absolute right-6 top-6 flex items-center gap-2 p-1.5 bg-slate-800/80 backdrop-blur border border-slate-700 rounded-lg shadow-xl">
                        <button onClick={() => setZoom(z => Math.max(0.2, z - 0.1))} className="w-8 h-8 flex items-center justify-center hover:bg-slate-700 rounded text-lg">-</button>
                        <span className="text-[10px] font-mono w-10 text-center text-slate-400 font-bold">{Math.round(zoom * 100)}%</span>
                        <button onClick={() => setZoom(z => Math.min(3, z + 0.1))} className="w-8 h-8 flex items-center justify-center hover:bg-slate-700 rounded text-lg">+</button>
                        <div className="w-px h-4 bg-slate-700 mx-1" />
                        <button onClick={() => setZoom(1)} className="px-2 text-[10px] font-bold text-blue-400 hover:text-blue-300">RESET</button>
                    </div>
                </div>}

                {/* Scrollable Canvas */}
                <div className="w-full h-full overflow-auto scrollbar-hide">
                    <div
                        className="relative bg-white shadow-xl origin-top-left transition-transform duration-75 ease-out"
                        style={{
                            width: `${figsize.w * DEFAULT_DPI}px`,
                            height: `${figsize.h * DEFAULT_DPI}px`,
                            transform: `scale(${zoom})`,
                        }}
                    >
                        {/* SVG content */}
                        <div
                            className="absolute inset-0 z-0 pointer-events-none"
                            dangerouslySetInnerHTML={{ __html: svgContent }}
                        />

                        {/* Overlay */}
                        {showOverlay && (
                            <div className="absolute inset-0 z-10">
                                <RecursiveGrid node={layout} path={[]} />
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default App;