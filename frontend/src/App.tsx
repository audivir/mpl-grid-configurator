import React, { useState, useEffect, useMemo } from "react";
import { debounce } from "lodash";
import GridOverlay from "./components/GridOverlay";
import Sidebar from "./components/Sidebar";
import FloatingControls from "./components/FloatingControls";
import PreviewOverlay from "./components/PreviewOverlay";
import { Layout, FigSize } from "./lib/layout";
import { useHistory } from "./lib/history";
import {
  STORAGE_KEYS,
  DEFAULT_LAYOUT,
  DEFAULT_FIGSIZE,
  API_BASE,
  DEFAULT_DPI,
  RENDER_DEBOUNCE,
  RESIZE_DEBOUNCE,
} from "./lib/const";
import { Toaster, toast } from "sonner";

/**
 * Extracts the FastAPI 'detail' string from a Response object
 */
const getErrorMessage = async (response: Response): Promise<string> => {
  try {
    const data = await response.json();
    // FastAPI puts the message in .detail
    // Sometimes it's a string, sometimes an array (for validation errors)
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return data.detail[0].msg;
    return "An unexpected error occurred.";
  } catch {
    return `Server Error: ${response.statusText}`;
  }
};

const App: React.FC = () => {
  const [funcs, setFuncs] = useState<string[]>([]);
  const [svgContent, setSvgContent] = useState<string>("");
  const [showOverlay, setShowOverlay] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
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
        try {
          const response = await fetch(`${API_BASE}/render`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ layout: l, figsize: [fs.w, fs.h] }),
          });

          if (!response.ok) {
            const errorMessage = await getErrorMessage(response);
            toast.error("Render Failed", {
              description: errorMessage,
              duration: 5000,
            });
            return;
          }

          const data = await response.json();
          setSvgContent(data.svg);
        } catch (e) {
          toast.error("Network Error", {
            description: "Could not connect to the Python backend.",
          });
        }
      }, RENDER_DEBOUNCE),
    []
  );

  const mergeCallback = async (p_a: string, p_b: string) => {
    try {
      const response = await fetch(`${API_BASE}/merge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          layout_data: { layout, figsize: [figsize.w, figsize.h] },
          path_a: p_a.split("-").slice(1).map(Number),
          path_b: p_b.split("-").slice(1).map(Number),
        }),
      });

      if (!response.ok) {
        const errorMessage = await getErrorMessage(response);
        toast.error("Merge Failed", {
          description: errorMessage,
          duration: 5000,
        });
        return;
      }

      const data = await response.json();
      // Update history with the new layout returned from backend
      setPresent(data.layout, figsize);
      setSvgContent(data.svg);
      toast.success("Merge successful!");
    } catch (e) {
      toast.error("Merging failed:", {
        description: "Could not connect to the Python backend.",
      });
    }
  };

  useEffect(() => {
    fetch(`${API_BASE}/functions`)
      .then((r) => r.json())
      .then((data) => setFuncs(data))
      .catch((err) => console.error("Could not fetch functions:", err));
  }, []);

  useEffect(() => {
    renderLayout(layout, figsize);
  }, [layout, figsize, renderLayout]);

  return (
    <>
      <Toaster theme="dark" position="bottom-right" expand={false} richColors />
      <div className="flex w-screen h-screen bg-[#0f172a] text-[#f1f5f9] font-sans overflow-hidden select-none">
        <Sidebar
          collapsed={!sidebarOpen}
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
          {showOverlay && (
            <FloatingControls
              sidebarOpen={sidebarOpen}
              setSidebarOpen={setSidebarOpen}
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

              {showOverlay &&
                (figsizePreview.w !== figsize.w ||
                  figsizePreview.h !== figsize.h) && ( // During dragging
                  <PreviewOverlay figsize={figsizePreview} dpi={DEFAULT_DPI} />
                )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
};

export default App;
