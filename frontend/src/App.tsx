import React, { useState, useEffect, useMemo } from "react";
import { debounce } from "lodash";
import { Toaster, toast } from "sonner";
import InitialLoader from "./components/InitialLoader";
import Sidebar from "./components/Sidebar";
import Workspace from "./components/Workspace";
import { api } from "./lib/api";
import {
  STORAGE_KEYS,
  DEFAULT_LAYOUT,
  DEFAULT_FIGSIZE,
  RENDER_DEBOUNCE,
} from "./lib/const";
import useHistory from "./lib/history";
import useInit from "./lib/init";
import { Layout, FigSize } from "./lib/layout";

const App: React.FC = () => {
  const [isInitializing, setIsInitializing] = useState(true);
  const [sessionToken, setSessionToken] = useState<string | null>(
    localStorage.getItem(STORAGE_KEYS.SESSION_TOKEN)
  );
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

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.FIGSIZE, JSON.stringify(figsize));
    localStorage.setItem(STORAGE_KEYS.LAYOUT, JSON.stringify(layout));
  }, [layout, figsize]);

  const [figsizePreview, setFigsizePreview] = useState<FigSize>(figsize);

  useEffect(() => {
    setFigsizePreview(figsize);
  }, [figsize]);

  const renderLayout = useMemo(
    () =>
      debounce(async (l: Layout, fs: FigSize, tok: string | null) => {
        const data = await api.render(l, fs, tok);
        if (data) setSvgContent(data.svg);
      }, RENDER_DEBOUNCE),
    []
  );

  const mergeCallback = async (pA: string, pB: string) => {
    const pathA = pA.split("-").slice(1).map(Number);
    const pathB = pB.split("-").slice(1).map(Number);

    const data = await api.merge(layout, figsize, pathA, pathB, sessionToken);

    if (data) {
      setPresent(data.layout, figsize);
      setSvgContent(data.svg);
      toast.success("Merge successful!");
    }
  };

  useEffect(() => {
    if (isInitializing || !sessionToken) return;
    renderLayout(layout, figsize, sessionToken);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layout, figsize, renderLayout]);

  // Consolidated Initialization
  useInit({
    setIsInitializing,
    sessionToken,
    setSessionToken,
    layout,
    figsize,
    renderLayout,
    setFuncs,
    setSvgContent,
  });

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

        <main className="relative flex-1 bg-[#0f172a] overflow-hidden">
          {isInitializing ? (
            <InitialLoader />
          ) : (
            <Workspace
              setPresent={setPresent}
              layout={layout}
              figsize={figsize}
              figsizePreview={figsizePreview}
              showOverlay={showOverlay}
              svgContent={svgContent}
              zoom={zoom}
              funcs={funcs}
              mergeCallback={mergeCallback}
            />
          )}
        </main>
      </div>
    </>
  );
};

export default App;
