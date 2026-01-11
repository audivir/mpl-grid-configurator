import React, { useState, useEffect } from "react";
import { Toaster } from "sonner";
import InitialLoader from "./components/InitialLoader";
import Sidebar from "./components/Sidebar";
import Workspace from "./components/Workspace";
import { useLayoutActions } from "./lib/actions";
import { STORAGE_KEYS, DEFAULT_LAYOUT, DEFAULT_FIGSIZE } from "./lib/const";
import useHistory from "./lib/history";
import useInit from "./lib/init";
import { FigSize } from "./lib/layout";
import { useRestructure } from "./lib/restructure";

const App: React.FC = () => {
  const [isInitializing, setIsInitializing] = useState(true);
  const [sessionToken, setSessionToken] = useState<string | null>(
    localStorage.getItem(STORAGE_KEYS.SESSION_TOKEN)
  );
  const [funcs, setFuncs] = useState<string[]>([]);
  const [svgContent, setSvgContent] = useState<string>("");
  const [showOverlay, setShowOverlay] = useState(true);
  const [zoom, setZoom] = useState(1);

  const history = useHistory({
    initialLayout: localStorage.getItem(STORAGE_KEYS.LAYOUT)
      ? JSON.parse(localStorage.getItem(STORAGE_KEYS.LAYOUT)!)
      : DEFAULT_LAYOUT,
    initialFigsize: localStorage.getItem(STORAGE_KEYS.FIGSIZE)
      ? JSON.parse(localStorage.getItem(STORAGE_KEYS.FIGSIZE)!)
      : DEFAULT_FIGSIZE,
  });

  const { state, setPresent } = history;
  const { layout, figsize } = state;

  useEffect(() => {
    if (typeof figsize !== "object") {
      setPresent(layout, DEFAULT_FIGSIZE);
    }
  }, [layout, figsize, setPresent]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.FIGSIZE, JSON.stringify(figsize));
    localStorage.setItem(STORAGE_KEYS.LAYOUT, JSON.stringify(layout));
  }, [layout, figsize]);

  const [figsizePreview, setFigsizePreview] = useState<FigSize>(figsize);

  useEffect(() => {
    setFigsizePreview(figsize);
  }, [figsize]);

  const { restructureCallback } = useRestructure({
    layout,
    figsize,
    sessionToken,
    setPresent,
    setSvgContent,
    executeAction: history.executeAction,
  });

  const actions = useLayoutActions({
    sessionToken,
    history,
    setSvgContent,
    restructureCallback,
  });

  // Consolidated Initialization
  useInit({
    setIsInitializing,
    sessionToken,
    setSessionToken,
    layout,
    figsize,
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
          zoom={zoom}
          setZoom={setZoom}
          showOverlay={showOverlay}
          setShowOverlay={setShowOverlay}
          svgContent={svgContent}
          setSvgContent={setSvgContent}
          history={history}
          actions={actions}
        />

        <main className="relative flex-1 bg-[#0f172a] overflow-hidden">
          {isInitializing ? (
            <InitialLoader />
          ) : (
            <Workspace
              layout={layout}
              figsize={figsize}
              figsizePreview={figsizePreview}
              showOverlay={showOverlay}
              svgContent={svgContent}
              setSvgContent={setSvgContent}
              zoom={zoom}
              funcs={funcs}
              actions={actions}
            />
          )}
        </main>
      </div>
    </>
  );
};

export default App;
