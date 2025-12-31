import React, { useState, useEffect, useMemo, DragEvent } from 'react';
import { Panel, Group, Separator, Layout as ResizableLayout } from 'react-resizable-panels';
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
    Grip
} from 'lucide-react';
import { cn } from 'react-lib-tools';

const API_BASE = "http://localhost:8765";
const DPI = 96;
const STORAGE_KEYS = {
    LAYOUT: 'plot-layout-v1',
    FIGSIZE: 'plot-figsize-v1'
};

type Orientation = 'row' | 'column';
type Layout = string | LayoutNode;

interface LayoutNode {
    orient: Orientation;
    children: [Layout, Layout];
    ratios: [number, number];
}

const App = () => {
    const [availableFuncs, setAvailableFuncs] = useState<string[]>([]);
    const [svgContent, setSvgContent] = useState<string>("");
    const [showOverlay, setShowOverlay] = useState(true);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [configCopied, setConfigCopied] = useState(false);
    const [svgCopied, setSvgCopied] = useState(false);
    const [zoom, setZoom] = useState(1);
    const [draggedPath, setDraggedPath] = useState<string | null>(null);

    // --- LOCAL STORAGE INITIALIZATION ---
    const [figsize, setFigsize] = useState<{ w: number, h: number }>(() => {
        const saved = localStorage.getItem(STORAGE_KEYS.FIGSIZE);
        return saved ? JSON.parse(saved) : { w: 8, h: 4 };
    });

    const [layout, setLayout] = useState<Layout>(() => {
        const saved = localStorage.getItem(STORAGE_KEYS.LAYOUT);
        return saved ? JSON.parse(saved) : "draw_empty";
    });

    // Sync state to local storage
    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.FIGSIZE, JSON.stringify(figsize));
    }, [figsize]);

    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.LAYOUT, JSON.stringify(layout));
    }, [layout]);

    // --- HANDLERS ---
    const handleReset = () => {
        if (window.confirm("Reset layout to default?")) {
            setLayout("draw_empty");
            setFigsize({ w: 8, h: 4 });
            localStorage.clear();
        }
    };

    const copyConfigToClipboard = async () => {
        await navigator.clipboard.writeText(JSON.stringify({ layout, figsize }, null, 2));
        setConfigCopied(true);
        setTimeout(() => setConfigCopied(false), 2000);
    };

    const copySvgToClipboard = async () => {
        await navigator.clipboard.writeText(svgContent);
        setSvgCopied(true);
        setTimeout(() => setSvgCopied(false), 2000);
    };

    const downloadSvg = () => {
        const blob = new Blob([svgContent], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'plot.svg';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const importFromClipboard = () => {
        const raw = window.prompt("Paste your JSON configuration here:");
        if (!raw) return;
        try {
            const parsed = JSON.parse(raw);
            if (parsed.layout && parsed.figsize) {
                setLayout(parsed.layout);
                setFigsize(parsed.figsize);
            } else {
                alert("Invalid format: Missing layout or figsize keys.");
            }
        } catch (e) {
            alert("Invalid JSON data.");
        }
    };

    // --- BACKEND SYNC ---
    useEffect(() => {
        fetch(`${API_BASE}/functions`)
            .then(r => r.json())
            .then(data => {
                setAvailableFuncs(data);
                if (data.length > 0 && layout === "draw_empty") {
                    setLayout(data[0]);
                }
            })
            .catch(e => console.error("Backend connection failed:", e));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const renderAll = useMemo(() => debounce(async (l: Layout, fs: { w: number, h: number }) => {
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
            console.error("Network Error:", e);
        }
    }, 400), []);

    useEffect(() => {
        renderAll(layout, figsize);
    }, [layout, figsize, renderAll]);

    // --- RECURSIVE GRID HELPERS ---
    const updateAtSubPath = (path: number[], updater: (node: Layout) => Layout) => {
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
    };

    const ratiosChanged = (oldRatios: [number, number], newRatios: [number, number]) => {
        const EPSILON = 0.01;
        return oldRatios.some((val, idx) => Math.abs(val - newRatios[idx]) > EPSILON);
    };

    const debouncedUpdateRatios = useMemo(
        () =>
            debounce((path: number[], newRatios: [number, number]) => {
                setLayout(prev => {
                    const next = cloneDeep(prev);

                    // Navigate to the target node
                    let target = next as LayoutNode;
                    if (path.length === 0) {
                        // Root node check
                        if (typeof next === 'string' || !ratiosChanged(next.ratios, newRatios)) return prev;
                        next.ratios = newRatios;
                    } else {
                        for (let i = 0; i < path.length - 1; i++) {
                            target = target.children[path[i]] as LayoutNode;
                        }
                        const lastIdx = path[path.length - 1];
                        const targetNode = target.children[lastIdx] as LayoutNode;

                        // GUARD: If ratios haven't really changed, return previous state object
                        // returning 'prev' (the same reference) prevents a React re-render
                        if (typeof targetNode === "string" || !ratiosChanged(targetNode.ratios, newRatios)) {
                            return prev;
                        }

                        targetNode.ratios = newRatios;
                    }
                    return next;
                });
            }, 100),
        []
    );

    const updateRatios = (rlayout: ResizableLayout) => {
        const path = Object.keys(rlayout)[0]
            .split("-")
            .slice(1, -1)
            .map(Number);
        const [left_up, right_down] = Object.values(rlayout);

        debouncedUpdateRatios(path, [left_up, right_down])
    };

    const splitLeaf = (path: number[], orient: Orientation) => {
        updateAtSubPath(path, (currentLeaf) => ({
            orient,
            ratios: [50, 50],
            children: [currentLeaf, currentLeaf]
        }));
    };

    const deleteNode = (path: number[]) => {
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

    const dragAnimation = (ev: DragEvent) => {
        const parent = (ev.currentTarget as Element).parentElement!;
        ev.dataTransfer.setDragImage(parent, 0, 0);
        const pathId = parent.parentElement!.parentElement!.id;
        setDraggedPath(pathId);
    };

    const handleSwap = (pathIdA: string, pathIdB: string) => {
        if (pathIdA === pathIdB) return;

        const pathA = pathIdA.split("-").map(Number);
        const pathB = pathIdB.split("-").map(Number);

        setLayout(prev => {
            const next = cloneDeep(prev);

            const getAt = (root: Layout, p: number[]) => {
                let curr = root;
                for (const i of p) curr = (curr as LayoutNode).children[i];
                return curr as LayoutNode;
            };

            const setAt = (root: Layout, p: number[], val: Layout) => {
                if (p.length === 0) return val;
                let curr = root;
                for (let i = 0; i < p.length - 1; i++) curr = (curr as LayoutNode).children[p[i]];
                (curr as LayoutNode).children[p[p.length - 1]] = val;
                return root;
            };

            const valA = cloneDeep(getAt(next, pathA));
            const valB = cloneDeep(getAt(next, pathB));

            setAt(next, pathA, valB);
            setAt(next, pathB, valA);

            return next;
        });
        // dont debounce rerender
        renderAll(layout, figsize);
    };
    const RecursiveGrid = ({ node, path }: { node: Layout, path: number[] }) => {
        const [isOver, setIsOver] = useState(false);
        if (typeof node === "string") {
            const pathId = path.join("-");
            return (
                <div
                    // className="relative w-full h-full border border-blue-500/10 group"
                    id={pathId}

                    // Full Surface Drop Logic
                    onDragOver={(e) => {
                        e.preventDefault();
                        setIsOver(true);
                    }}
                    onDragLeave={() => setIsOver(false)}
                    onDrop={(e) => {
                        e.preventDefault();
                        setIsOver(false);
                        if (draggedPath) handleSwap(draggedPath, pathId);
                    }}
                    className={cn(
                        "relative w-full h-full border border-blue-500/10 transition-all pointer-events-auto",
                        isOver ? "bg-blue-500/30 border-blue-500 border-2 z-20" : null
                    )}
                >

                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <button
                            title="Split Horizontally"
                            className="absolute top-2 right-2 p-1.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-500 hover:bg-blue-500 hover:text-white transition-all pointer-events-auto opacity-0 group-hover:opacity-100"
                            onClick={() => splitLeaf(path, "row")}
                            style={{
                                transform: `scale(${1 / zoom})`,
                                transformOrigin: 'top right',
                            }}
                        >
                            <Columns size={14} />
                        </button>

                        <div className="flex items-center gap-1 p-1 bg-white/95 border border-slate-200 rounded-md shadow-lg pointer-events-auto transform transition-transform group-hover:scale-105"
                            style={{
                                transform: `scale(${1 / zoom})`,
                                transformOrigin: 'center',
                            }}>
                            {path.length > 0 && (
                                <button
                                    draggable
                                    className="p-1 text-slate-500 hover:bg-slate-50 rounded transition-colors"
                                    onDragStart={dragAnimation}
                                    onDragEnd={() => setDraggedPath(null)}
                                >
                                    <Grip size={12} />
                                </button>
                            )}
                            <select
                                className="text-[11px] font-semibold text-slate-800 bg-transparent border-none focus:ring-0 outline-none px-1"
                                value={node}
                                onChange={e => updateAtSubPath(path, () => e.target.value)}
                            >
                                {availableFuncs.map(f => <option key={f} value={f}>{f}</option>)}
                            </select>
                            {path.length > 0 && (
                                <button
                                    className="p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
                                    onClick={() => deleteNode(path)}
                                >
                                    <Trash2 size={12} />
                                </button>
                            )}
                        </div>

                        <button
                            title="Split Vertically"
                            className="absolute bottom-2 left-2 p-1.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-500 hover:bg-blue-500 hover:text-white transition-all pointer-events-auto opacity-0 group-hover:opacity-100"
                            onClick={() => splitLeaf(path, "column")}
                            style={{
                                transform: `scale(${1 / zoom})`,
                                transformOrigin: 'bottom left',
                            }}
                        >
                            <Rows size={14} />
                        </button>
                    </div>
                </div >
            );
        }

        const pathId = [0, ...path].join("-");
        return (
            <Group
                orientation={node.orient === "row" ? "horizontal" : "vertical"}
                className="w-full h-full"
                onLayoutChange={updateRatios}
            >
                <Panel defaultSize={node.ratios[0]} id={pathId + "-0"}>
                    <RecursiveGrid node={node.children[0]} path={[...path, 0]} />
                </Panel>
                <Separator className={cn(
                    "bg-slate-200 hover:bg-blue-400 active:bg-blue-600 transition-colors",
                    node.orient === "row" ? "w-1" : "h-1"
                )} />
                <Panel defaultSize={node.ratios[1]} id={pathId + "-1"}>
                    <RecursiveGrid node={node.children[1]} path={[...path, 1]} />
                </Panel>
            </Group>
        );
    };

    const buttonClass = "flex items-center gap-3 w-full py-2 px-1 text-slate-400 hover:text-blue-400 transition-colors text-sm font-medium"
    const width = `${figsize.w * DPI}px`
    const height = `${figsize.h * DPI}px`


    return (
        <div className="flex w-screen h-screen bg-[#0f172a] text-[#f1f5f9] font-sans overflow-hidden">
            {/* SIDEBAR */}
            <aside className={cn(
                "bg-[#1e293b] border-r border-slate-700 transition-all duration-300 ease-in-out shrink-0 overflow-hidden",
                sidebarOpen ? "w-[260px] p-6" : "w-0 p-0"
            )}>
                <div className="flex items-center gap-3 mb-8 pb-4 border-b border-slate-700">
                    <Settings size={20} className="text-blue-400" />
                    <h3 className="font-bold text-sm tracking-tight">GRID CONFIGURATOR</h3>
                </div>

                <div className="space-y-6">
                    <div className="space-y-3">
                        <div className="flex justify-between text-xs text-slate-400 font-medium">
                            <span>WIDTH</span>
                            <span className="text-blue-400">{figsize.w}</span>
                        </div>
                        <input type="range" min="4" max="24" step="0.5" value={figsize.w} onChange={e => setFigsize({ ...figsize, w: +e.target.value })} className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500" />
                    </div>

                    <div className="space-y-3">
                        <div className="flex justify-between text-xs text-slate-400 font-medium">
                            <span>HEIGHT</span>
                            <span className="text-blue-400">{figsize.h}</span>
                        </div>
                        <input type="range" min="2" max="18" step="0.5" value={figsize.h} onChange={e => setFigsize({ ...figsize, h: +e.target.value })} className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500" />
                    </div>

                    <div className="pt-2 space-y-1">
                        <label className="flex items-center gap-3 py-2 px-1 cursor-pointer hover:text-white transition-colors">
                            <input type="checkbox" checked={showOverlay} onChange={e => setShowOverlay(e.target.checked)} className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500" />
                            <span className="text-sm font-medium">Layout Overlay</span>
                        </label>

                        <button
                            onClick={copyConfigToClipboard}
                            className={buttonClass}
                        >
                            {configCopied ? <Check size={16} className="text-green-400" /> : <ClipboardCopy size={16} />}
                            {configCopied ? "Copied!" : "Copy Configuration"}
                        </button>

                        <button
                            onClick={importFromClipboard}
                            className={buttonClass}
                        >
                            <Import size={16} />
                            Import Configuration
                        </button>

                        <button
                            onClick={copySvgToClipboard}
                            className={buttonClass}
                        >
                            {svgCopied ? <Check size={16} className="text-green-400" /> : <ClipboardCopy size={16} />}
                            {svgCopied ? "Copied!" : "Copy SVG"}
                        </button>

                        <button
                            onClick={downloadSvg}
                            className={buttonClass}
                        >
                            <Download size={16} />
                            Download SVG
                        </button>

                        <button
                            onClick={handleReset}
                            className={cn(buttonClass, "hover:text-red-400")}
                        >
                            <RotateCcw size={16} />
                            Reset All Progress
                        </button>
                    </div>
                </div>
            </aside>

            {/* VIEWPORT AREA */}
            <main className="relative flex-1 bg-[#0f172a] overflow-hidden flex flex-col">
                {/* UI LAYER: Stays fixed on top of the scrolling area */}
                <div className="absolute inset-0 z-50 pointer-events-none">
                    {/* Sticky Sidebar Button */}
                    <button
                        className="pointer-events-auto absolute left-6 top-6 p-2.5 bg-slate-800 border border-slate-700 rounded-xl hover:bg-slate-700 text-white shadow-2xl transition-all"
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                    >
                        <SidebarIcon size={20} />
                    </button>

                    {/* Sticky Zoom Controls */}
                    <div className="pointer-events-auto absolute right-6 top-6 flex items-center gap-2 p-1.5 bg-slate-800/90 backdrop-blur border border-slate-700 rounded-xl shadow-2xl">
                        <button onClick={() => setZoom(z => Math.max(0.2, z - 0.1))} className="p-2 hover:bg-slate-700 rounded text-white">-</button>
                        <span className="text-xs font-mono w-12 text-center text-slate-300 font-bold">{Math.round(zoom * 100)}%</span>
                        <button onClick={() => setZoom(z => Math.min(3, z + 0.1))} className="p-2 hover:bg-slate-700 rounded text-white">+</button>
                        <div className="w-px h-4 bg-slate-700 mx-1" />
                        <button onClick={() => setZoom(1)} className="px-2 py-1 text-[10px] font-bold text-blue-400 hover:text-blue-300">RESET</button>
                    </div>
                </div>

                {/* add the scrollable viewport */}
                <div className="flex-1 overflow-auto scrollbar-thin scrollbar-thumb-slate-700">
                    <div className="w-full h-full">
                        <div
                            className="relative bg-white shadow-xl rounded-sm shrink-0"
                            style={{
                                width,
                                height,
                                transform: `scale(${zoom})`,
                                transformOrigin: 'top left',
                            }}
                        >
                            <div className="absolute inset-0 z-0 pointer-events-none" dangerouslySetInnerHTML={{ __html: svgContent }} />
                            {showOverlay && (
                                <div className="absolute inset-0 z-10 pointer-events-none">
                                    <RecursiveGrid node={layout} path={[]} />
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default App;
