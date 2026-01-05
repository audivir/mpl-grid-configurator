import React, { useState, useEffect, useMemo } from "react";
import { debounce } from "lodash";
import GridOverlay from "./components/GridOverlay";
import Sidebar from "./components/Sidebar";
import PreviewOverlay from "./components/PreviewOverlay";
import { Layout, FigSize } from "./lib/layout";
import { useHistory } from "./lib/history";
import {
  STORAGE_KEYS,
  DEFAULT_LAYOUT,
  DEFAULT_FIGSIZE,
  DEFAULT_DPI,
  RENDER_DEBOUNCE,
  RESIZE_DEBOUNCE,
} from "./lib/const";
import { Toaster, toast } from "sonner";
import { api } from "./lib/api";

const App: React.FC = () => {
  const [funcs, setFuncs] = useState<string[]>([]);
  const [svgContent, setSvgContent] = useState<string>("");
  const [showOverlay, setShowOverlay] = useState(true);
  const [zoom, setZoom] = useState(1);

  const { state, setPresent, undo, redo, canUndo, canRedo, resetHistory } =
    useHistory(
      localStorage.getItem(STORAGE_KEYS.LAYOUT)
        ? JSON.parse(localStorage.getItem(STORAGE_KEYS.LAYOUT)!)
        : DEFAULT_LAYOUT,
      localStorage.getItem(STORAGE_KEYS.FIGSIZE)
        ? JSON.parse(localStorage.getItem(STORAGE_KEYS.FIGSIZE)!)
        : DEFAULT_FIGSIZE
    );

  const { layout, figsize } = state;
  const [figsizePreview, setFigsizePreview] = useState<FigSize>(figsize);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.FIGSIZE, JSON.stringify(figsize));
    localStorage.setItem(STORAGE_KEYS.LAYOUT, JSON.stringify(layout));
  }, [layout, figsize]);

  useEffect(() => {
    setFigsizePreview(figsize);
  }, [figsize]);

  const renderLayout = useMemo(
    () =>
      debounce(async (l: Layout, fs: FigSize) => {
        const data = await api.render(l, [fs.w, fs.h]);
        if (data) setSvgContent(data.svg);
      }, RENDER_DEBOUNCE),
    []
  );

  const mergeCallback = async (p_a: string, p_b: string) => {
    const layoutData = { layout, figsize: [figsize.w, figsize.h] };
    const pathA = p_a.split("-").slice(1).map(Number);
    const pathB = p_b.split("-").slice(1).map(Number);

    const data = await api.merge(layoutData, pathA, pathB);

    if (data) {
      setPresent(data.layout, figsize);
      setSvgContent(data.svg);
      toast.success("Merge successful!");
    }
  };

  useEffect(() => {
    api.getFunctions().then((data) => {
      if (data) setFuncs(data);
    });
  }, []);

  useEffect(() => {
    renderLayout(layout, figsize);
  }, [layout, figsize, renderLayout]);

  return (
    <>
      <Toaster theme="dark" position="top-right" expand={false} richColors />
      <div className="flex w-screen h-screen bg-[#0f172a] text-[#f1f5f9] font-sans overflow-hidden select-none">
        <Sidebar
          layout={layout}
          figsize={figsize}
          figsizePreview={figsizePreview}
          setFigsizePreview={setFigsizePreview}
          commitFigsize={() => setPresent(layout, figsizePreview)}
          zoom={zoom}
          setZoom={setZoom}
          showOverlay={showOverlay}
          setShowOverlay={setShowOverlay}
          handleReset={(l: Layout, fs: FigSize) => resetHistory(l, fs)}
          svgContent={svgContent}
          canUndo={canUndo}
          canRedo={canRedo}
          onUndo={undo}
          onRedo={redo}
        />

        {/* Workspace Viewport */}
        <main className="relative flex-1 bg-[#0f172a] overflow-hidden">
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

              {showOverlay && (
                <div className="absolute inset-0 z-10">
                  <GridOverlay
                    setPresent={setPresent}
                    layout={layout}
                    figsize={figsize}
                    funcs={funcs}
                    zoom={zoom}
                    resizeDebounce={RESIZE_DEBOUNCE}
                    mergeCallback={mergeCallback}
                  />
                </div>
              )}

              {/* Resizing preview */}
              {showOverlay &&
                (figsizePreview.w !== figsize.w ||
                  figsizePreview.h !== figsize.h) && ( // During dragging
                  <PreviewOverlay figsize={figsizePreview} />
                )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
};

export default App;
