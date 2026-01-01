import React, { useState, useEffect, useMemo } from "react";
import { debounce } from "lodash";
import GridOverlay from "./components/GridOverlay";
import Sidebar from "./components/Sidebar";
import { Layout, FigSize } from "./lib/layout";
import FloatingControls from "./components/FloatingControls";

const API_BASE = "http://localhost:8765";
const DEFAULT_DPI = 96;
const RESIZE_DEBOUNCE = 50;
const RENDER_DEBOUNCE = 150;
const STORAGE_KEYS = {
  LAYOUT: "plot-layout-v1",
  FIGSIZE: "plot-figsize-v1",
} as const;

const App: React.FC = () => {
  const [availableFuncs, setAvailableFuncs] = useState<string[]>([]);
  const [svgContent, setSvgContent] = useState<string>("");
  const [showOverlay, setShowOverlay] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [zoom, setZoom] = useState(1);

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

  const renderLayout = useMemo(
    () =>
      debounce(async (l: Layout, fs: FigSize) => {
        try {
          const response = await fetch(`${API_BASE}/render`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ layout: l, figsize: [fs.w, fs.h] }),
          });
          if (response.ok) {
            const data = await response.json();
            setSvgContent(data.svg);
          }
        } catch (e) {
          console.error("Rendering failed:", e);
        }
      }, RENDER_DEBOUNCE),
    []
  );

  useEffect(() => {
    fetch(`${API_BASE}/functions`)
      .then((r) => r.json())
      .then((data) => {
        setAvailableFuncs(data);
      })
      .catch((err) => console.error("Could not fetch functions:", err));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    renderLayout(layout, figsize);
  }, [layout, figsize, renderLayout]);

  return (
    <div className="flex w-screen h-screen bg-[#0f172a] text-[#f1f5f9] font-sans overflow-hidden select-none">
      <Sidebar
        collapsed={!sidebarOpen}
        layout={layout}
        setLayout={setLayout}
        figsize={figsize}
        setFigsize={setFigsize}
        showOverlay={showOverlay}
        setShowOverlay={setShowOverlay}
        handleReset={() => {
          setLayout("draw_empty");
          setFigsize({ w: 8, h: 4 });
        }}
        svgContent={svgContent}
      />

      {/* Workspace Viewport */}
      <main className="relative flex-1 bg-[#0f172a] overflow-hidden">
        {showOverlay && (
          <FloatingControls
            sidebarOpen={sidebarOpen}
            setSidebarOpen={setSidebarOpen}
            zoom={zoom}
            setZoom={setZoom}
          />
        )}

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
                  layout={layout}
                  setLayout={setLayout}
                  funcs={availableFuncs}
                  zoom={zoom}
                  resizeDebounce={RESIZE_DEBOUNCE}
                />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
