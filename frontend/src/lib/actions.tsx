import { useCallback } from "react";
import { toast } from "sonner";
import { FullResponse } from "../lib/api";
import {
  Layout,
  LPath,
  FigureSize,
  Orient,
  RestructuredLayout,
  Ratios,
} from "../lib/layout";
import { History } from "./history";
import { apiCalls } from "./apiCalls";

interface UseLayoutActionsProps {
  sessionToken: string | null;
  history: History;
  setSvgContent: (svg: string) => void;
  restructureCallback: (restructuredLayout: RestructuredLayout) => void;
}

export interface LayoutActions {
  delete: (path: LPath) => Promise<void>;
  merge: (pAId: string, pBId: string) => Promise<void>;
  insert: (
    path: LPath,
    orient: Orient,
    ratios: Ratios,
    value: string
  ) => Promise<void>;
  replace: (path: LPath, value: string) => Promise<void>;
  rotate: (path: LPath) => Promise<void>;
  resize: (targetSize: FigureSize) => Promise<void>;
  restructure: (resizedLayout: RestructuredLayout) => void;
  split: (path: LPath, orient: Orient) => Promise<void>;
  swap: (pA: string, pB: string) => Promise<void>;
  reset: (l: Layout, fs: FigureSize, msg?: string) => Promise<void>;
}

export const useLayoutActions = ({
  sessionToken,
  history,
  setSvgContent,
  restructureCallback,
}: UseLayoutActionsProps): LayoutActions => {
  // Helper to handle both executeAction and Undo/Redo results
  const syncUI = useCallback(
    (res: FullResponse | null, msg?: string) => {
      if (res) {
        setSvgContent(res.svg);
        if (msg) toast.success(msg);
      }
    },
    [setSvgContent]
  );

  return {
    delete: async (path: LPath) => {
      const res = await history.executeAction("DELETE", (l, f) =>
        apiCalls.delete(l, path, sessionToken)
      );
      res && syncUI(res, "Deleted successfully");
    },

    merge: async (pAId: string, pBId: string) => {
      if (pAId === pBId) {
        toast.info("Paths are the same, nothing to do");
        return;
      }
      if (pAId.slice(0, -2) === pBId.slice(0, -2)) {
        toast.info("Paths are already siblings, nothing to do");
        return;
      }
      const pathA = pAId.split("-").slice(1).map(Number) as LPath;
      const pathB = pBId.split("-").slice(1).map(Number) as LPath;
      const res = await history.executeAction("MERGE", (l, f) =>
        apiCalls.merge(pathA, pathB, sessionToken)
      );
      res && syncUI(res, "Merged successfully");
    },

    insert: async (
      path: LPath,
      orient: Orient,
      ratios: Ratios,
      value: string
    ) => {
      const res = await history.executeAction("INSERT", (l, f) =>
        apiCalls.insert(path, orient, ratios, value, sessionToken)
      );
      res && syncUI(res, "Inserted successfully");
    },

    replace: async (path: LPath, value: string) => {
      const res = await history.executeAction("REPLACE", (l, f) =>
        apiCalls.replace(l, path, value, sessionToken)
      );
      res && syncUI(res, "Replaced successfully");
    },

    resize: async (targetSize: FigureSize) => {
      const res = await history.executeAction("RESIZE", (l, f) =>
        apiCalls.resize(f, targetSize, sessionToken)
      );
      res && syncUI(res, "Resized successfully");
    },

    restructure: async (restructuredLayout: RestructuredLayout) => {
      restructureCallback(restructuredLayout);
    },

    rotate: async (path: LPath) => {
      const res = await history.executeAction("ROTATE", (l, f) =>
        apiCalls.rotate(path, sessionToken)
      );
      res && syncUI(res, "Rotated successfully");
    },

    split: async (path: LPath, orient: Orient) => {
      const res = await history.executeAction("SPLIT", (l, f) =>
        apiCalls.split(path, orient, sessionToken)
      );
      res && syncUI(res, "Split successfully");
    },

    swap: async (pA: string, pB: string) => {
      if (pA === pB) {
        toast.info("Paths are the same, nothing to do");
        return;
      }
      const pathA = pA.split("-").slice(1).map(Number);
      const pathB = pB.split("-").slice(1).map(Number);
      const res = await history.executeAction("SWAP", (l, f) =>
        apiCalls.swap(pathA, pathB, sessionToken)
      );
      res && syncUI(res, "Swapped successfully");
    },

    reset: async (layout: Layout, figsize: FigureSize, msg?: string) => {
      const res = await history.executeAction("RESET", (l, f) =>
        apiCalls.render(layout, figsize, sessionToken)
      );
      res && syncUI(res, msg);
    },
  };
};
