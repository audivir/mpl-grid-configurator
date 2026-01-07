import { SetStateAction, useEffect, useRef } from "react";
import { api } from "./api";
import { STORAGE_KEYS } from "./const";
import { Layout, FigSize } from "./layout";

interface InitProps {
  setIsInitializing: (v: SetStateAction<boolean>) => void;
  sessionToken: string | null;
  setSessionToken: (v: SetStateAction<string | null>) => void;
  layout: Layout;
  figsize: FigSize;
  renderLayout: (
    l: Layout,
    fs: FigSize,
    tok: string | null
  ) => Promise<void> | undefined;
  setFuncs: (v: SetStateAction<string[]>) => void;
  setSvgContent: (v: SetStateAction<string>) => void;
}

const useInit = ({
  setIsInitializing,
  setFuncs,
  sessionToken,
  setSessionToken,
  layout,
  figsize,
  renderLayout,
  setSvgContent,
}: InitProps) => {
  const hasInitialized = useRef(false);

  useEffect(() => {
    // Only run once
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const performInit = async () => {
      try {
        const funcsData = await api.getFunctions();
        if (funcsData) setFuncs(funcsData);

        let activeToken = sessionToken;
        let createNewSession = false;

        // 1. Health Check existing token
        if (activeToken) {
          const ok = await api.healthCheck(activeToken);
          if (ok) {
            // Token is valid, perform initial render
            await renderLayout(layout, figsize, activeToken);
          } else {
            createNewSession = true;
            localStorage.removeItem(STORAGE_KEYS.SESSION_TOKEN);
            setSessionToken(null);
            activeToken = null;
          }
        }

        // 2. Create session if needed
        if (!activeToken || createNewSession) {
          const sessionData = await api.createSession(layout, figsize);
          if (sessionData) {
            localStorage.setItem(STORAGE_KEYS.SESSION_TOKEN, sessionData.token);
            setSessionToken(sessionData.token);
            setSvgContent(sessionData.svg);
          }
        }
      } catch (err) {
        console.error("Initialization error:", err);
      } finally {
        setIsInitializing(false);
      }
    };

    performInit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // only runs on mount
};

export default useInit;
