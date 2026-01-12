// frontend/src/lib/useRestructure.ts
import { useState, useEffect, useMemo } from "react";
import { debounce } from "lodash";
import { toast } from "sonner";
import { FullResponse } from "./api";
import { RESIZE_DEBOUNCE, RESIZE_EPSILON } from "./const";
import {
  Layout,
  FigureSize,
  Resize,
  getNode,
  RestructureInfo,
  RestructuredLayout,
  Ratios,
} from "./layout";
import { HistoryActionType } from "./history";
import { ApiCall, apiCalls } from "./apiCalls";

interface UseRestructureProps {
  layout: Layout;
  figsize: FigureSize;
  sessionToken: string | null;
  setSvgContent: (svg: string) => void;
  executeAction: (
    type: HistoryActionType,
    apiCallBuilder: (l: Layout, f: FigureSize) => ApiCall<FullResponse | null>
  ) => Promise<FullResponse | null>;
}

/**
 * Checks if the ratios have changed by more than a small epsilon
 */
const didResize = (oldRatios: Ratios, newRatios: Ratios) => {
  return oldRatios.some(
    (val, idx) => Math.abs(val - newRatios[idx]) > RESIZE_EPSILON
  );
};

export const useRestructure = ({
  layout,
  figsize,
  sessionToken,
  setSvgContent,
  executeAction,
}: UseRestructureProps) => {
  const [rowRestructure, setRowRestructure] = useState<Resize>(null);
  const [columnRestructure, setColumnRestructure] = useState<Resize>(null);

  const debouncedSetRowRestructure = useMemo(
    () => debounce(setRowRestructure, RESIZE_DEBOUNCE),
    []
  );
  const debouncedSetColumnRestructure = useMemo(
    () => debounce(setColumnRestructure, RESIZE_DEBOUNCE),
    []
  );

  useEffect(() => {
    if (!rowRestructure && !columnRestructure) return;

    let rowRestructureInfo: RestructureInfo | null = null;
    let columnRestructureInfo: RestructureInfo | null = null;

    if (rowRestructure) {
      const [rowParentPathId, [rowLeftUp, rowRightDown]] = rowRestructure;
      const rowParentPath = rowParentPathId.split("-").slice(1).map(Number);
      rowRestructureInfo = [rowParentPath, [rowLeftUp, rowRightDown]];
    }
    if (columnRestructure) {
      const [columnParentPathId, [columnLeftUp, columnRightDown]] =
        columnRestructure;
      const columnParentPath = columnParentPathId
        .split("-")
        .slice(1)
        .map(Number);
      columnRestructureInfo = [
        columnParentPath,
        [columnLeftUp, columnRightDown],
      ];
    }

    executeAction("RESTRUCTURE", (l, f) =>
      apiCalls.restructure(
        l,
        rowRestructureInfo,
        columnRestructureInfo,
        sessionToken
      )
    )
      .then((res) => {
        if (res) {
          setSvgContent(res.svg);
          toast.success("Restructured successfully");
        }
      })
      .finally(() => {
        setColumnRestructure(null);
        setRowRestructure(null);
      });
  }, [
    rowRestructure,
    columnRestructure,
    figsize,
    sessionToken,
    setSvgContent,
    executeAction,
  ]);

  const restructureCallback = (restructuredLayout: RestructuredLayout) => {
    const firstKey = Object.keys(restructuredLayout)[0];
    const parentPathId = firstKey.slice(0, -2);
    const parentPath = parentPathId.split("-").slice(1).map(Number);
    const [leftUp, rightDown] = Object.values(restructuredLayout);
    const parentNode = getNode(layout, parentPath);
    const orient = parentNode.orient;

    if (!didResize(parentNode.ratios, [leftUp, rightDown])) {
      return;
    }

    const prevValue = orient === "row" ? rowRestructure : columnRestructure;
    const debouncedSetter =
      orient === "row"
        ? debouncedSetRowRestructure
        : debouncedSetColumnRestructure;

    if (prevValue) {
      const [prevLeftUp, prevRightDown] = prevValue[1];
      if (!didResize([prevLeftUp, prevRightDown], [leftUp, rightDown])) {
        return;
      }
    }

    debouncedSetter([parentPathId, [leftUp, rightDown]]);
  };

  return { restructureCallback };
};
