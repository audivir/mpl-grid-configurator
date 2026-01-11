import { useCallback } from "react";
import { toast } from "sonner";
import { FullResponse } from "../lib/api";
import {
  Layout,
  FigSize,
  Orientation,
  RestructuredLayout,
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
  delete: (path: number[]) => Promise<void>;
  merge: (pA: string, pB: string) => Promise<void>;
  insert: (
    path: number[],
    orient: Orientation,
    ratios: number[],
    value: string
  ) => Promise<void>;
  replace: (path: number[], value: string) => Promise<void>;
  rotate: (path: number[]) => Promise<void>;
  resize: (targetSize: FigSize) => Promise<void>;
  restructure: (resizedLayout: RestructuredLayout) => void;
  split: (path: number[], orient: Orientation) => Promise<void>;
  swap: (pA: string, pB: string) => Promise<void>;
  reset: (l: Layout, fs: FigSize, msg?: string) => Promise<void>;
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
    delete: async (path: number[]) => {
      const res = await history.executeAction("DELETE", (l, f) =>
        apiCalls.delete(l, path, sessionToken)
      );
      res && syncUI(res, "Deleted successfully");
    },

    merge: async (pA: string, pB: string) => {
      if (pA === pB) return;
      const pathA = pA.split("-").slice(1).map(Number);
      const pathB = pB.split("-").slice(1).map(Number);
      const res = await history.executeAction("MERGE", (l, f) =>
        apiCalls.merge(pathA, pathB, sessionToken)
      );
      res && syncUI(res, "Merged successfully");
    },

    insert: async (
      path: number[],
      orient: Orientation,
      ratios: number[],
      value: string
    ) => {
      const res = await history.executeAction("INSERT", (l, f) =>
        apiCalls.insert(path, orient, ratios, value, sessionToken)
      );
      res && syncUI(res, "Inserted successfully");
    },

    replace: async (path: number[], value: string) => {
      const res = await history.executeAction("REPLACE", (l, f) =>
        apiCalls.replace(l, path, value, sessionToken)
      );
      res && syncUI(res, "Replaced successfully");
    },

    resize: async (targetSize: FigSize) => {
      const res = await history.executeAction("RESIZE", (l, f) =>
        apiCalls.resize(f, targetSize, sessionToken)
      );
      res && syncUI(res, "Resized successfully");
    },

    restructure: async (restructuredLayout: RestructuredLayout) => {
      restructureCallback(restructuredLayout);
    },

    rotate: async (path: number[]) => {
      const res = await history.executeAction("ROTATE", (l, f) =>
        apiCalls.rotate(path, sessionToken)
      );
      res && syncUI(res, "Rotated successfully");
    },

    split: async (path: number[], orient: Orientation) => {
      const res = await history.executeAction("SPLIT", (l, f) =>
        apiCalls.split(path, orient, sessionToken)
      );
      res && syncUI(res, "Split successfully");
    },

    swap: async (pA: string, pB: string) => {
      const pathA = pA.split("-").slice(1).map(Number);
      const pathB = pB.split("-").slice(1).map(Number);
      if (pathA === pathB) return;
      const res = await history.executeAction("SWAP", (l, f) =>
        apiCalls.swap(pathA, pathB, sessionToken)
      );
      res && syncUI(res, "Swapped successfully");
    },

    reset: async (layout: Layout, figsize: FigSize, msg?: string) => {
      const res = await history.executeAction("RESET", (l, f) =>
        apiCalls.render(layout, figsize, sessionToken)
      );
      res && syncUI(res, msg);
    },
  };
};
