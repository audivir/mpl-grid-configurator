import {
  useCallback,
  useMemo,
  useState,
  useEffect,
  SetStateAction,
} from "react";
import { cloneDeep, debounce } from "lodash";
import {
  getNode,
  getLeaf,
  setNode,
  Layout,
  Resize,
  Orientation,
} from "./layout";
import { Layout as ResizedLayout } from "react-resizable-panels";

const RESIZE_EPSILON = 0.01;

interface GridDesignProps {
  layout: Layout;
  setLayout: (v: SetStateAction<Layout>) => void;
  resizeDebounce?: number;
}

/**
 * Checks if the ratios have changed by more than a small epsilon
 */
const didResize = (
  oldRatios: [number, number],
  newRatios: [number, number]
) => {
  return oldRatios.some(
    (val, idx) => Math.abs(val - newRatios[idx]) > RESIZE_EPSILON
  );
};

const useGridCallbacks = ({
  layout,
  setLayout,
  resizeDebounce,
}: GridDesignProps) => {
  const [rowResize, setRowResize] = useState<Resize>(null);
  const [columnResize, setColumnResize] = useState<Resize>(null);

  const updateAtSubPath = useCallback(
    (path: number[], updater: (node: Layout) => Layout) => {
      setLayout((prev) => {
        const next = cloneDeep(prev);
        // if root, set root
        if (path.length === 0) return updater(next);
        // else, replace node as parent's child
        const parentPath = path.slice(0, -1);
        const parentNode = getNode(next, parentPath);
        const currIx = path[path.length - 1];
        parentNode.children[currIx] = updater(parentNode.children[currIx]);
        return next;
      });
    },
    [setLayout]
  );

  const debouncedSetRowResize = useMemo(
    () => debounce(setRowResize, resizeDebounce),
    [resizeDebounce]
  );
  const debouncedSetColumnResize = useMemo(
    () => debounce(setColumnResize, resizeDebounce),
    [resizeDebounce]
  );

  // follow changes and update layout
  useEffect(() => {
    if (!rowResize && !columnResize) return;

    setLayout((prev) => {
      const next = cloneDeep(prev);
      if (rowResize) {
        const [rowParentPathId, [rowLeftUp, rowRightDown]] = rowResize;
        const rowParentPath = rowParentPathId.split("-").slice(1).map(Number);
        const rowParentNode = getNode(next, rowParentPath);
        rowParentNode.ratios = [rowLeftUp, rowRightDown];
      }
      if (columnResize) {
        const [columnParentPathId, [columnLeftUp, columnRightDown]] =
          columnResize;
        const columnParentPath = columnParentPathId
          .split("-")
          .slice(1)
          .map(Number);
        const columnParentNode = getNode(next, columnParentPath);
        columnParentNode.ratios = [columnLeftUp, columnRightDown];
      }
      return next;
    });
  }, [rowResize, columnResize, setLayout]);

  const handleResize = (resizedLayout: ResizedLayout) => {
    const parentPathId = Object.keys(resizedLayout)[0].slice(undefined, -2);
    const parentPath = parentPathId.split("-").slice(1).map(Number);
    const [leftUp, rightDown] = Object.values(resizedLayout);
    const parentNode = getNode(layout, parentPath);
    const orient = parentNode.orient;

    if (!didResize(parentNode.ratios, [leftUp, rightDown])) {
      return;
    }

    const prevValue = orient === "row" ? rowResize : columnResize;
    const debouncedSetter =
      orient === "row" ? debouncedSetRowResize : debouncedSetColumnResize;

    if (prevValue) {
      const [prevLeftUp, prevRightDown] = prevValue[1];
      if (!didResize([prevLeftUp, prevRightDown], [leftUp, rightDown])) {
        return;
      }
    }

    debouncedSetter([parentPathId, [leftUp, rightDown]]);
  };

  const handleLeaf = (path: number[], value: string) => {
    updateAtSubPath(path, (currentLeaf) => value);
  };

  const handleSplit = (path: number[], orient: Orientation) => {
    updateAtSubPath(path, (currentLeaf) => ({
      orient,
      ratios: [50, 50],
      children: [currentLeaf, currentLeaf],
    }));
  };

  const handleMerge = (pathIdA: string, pathIdB: string) => {
    console.log("merge", pathIdA, pathIdB);
  };

  const handleDelete = (path: number[]) => {
    if (path.length === 0) throw new Error("Cannot delete root");

    const parentPath = path.slice(0, -1);
    const currIx = path[path.length - 1];
    const parentIx = path[path.length - 2];
    const siblingIx = currIx === 0 ? 1 : 0;
    const siblingPath = [...parentPath, siblingIx];

    setLayout((prev) => {
      const next = cloneDeep(prev);
      const siblingLeaf = getLeaf(next, siblingPath);
      // if parent is root, return sibling
      if (parentPath.length === 0) return siblingLeaf;
      // else replace parent with sibling
      const grandparentPath = parentPath.slice(0, -1);
      const grandparentNode = getNode(next, grandparentPath);
      grandparentNode.children[parentIx] = siblingLeaf;
      return next;
    });
  };

  const handleSwap = (pathIdA: string, pathIdB: string) => {
    // do nothing if paths are the same
    if (pathIdA === pathIdB) return;
    const pathA = pathIdA.split("-").slice(1).map(Number);
    const pathB = pathIdB.split("-").slice(1).map(Number);

    setLayout((prev) => {
      const next = cloneDeep(prev);
      if (typeof next === "string")
        throw new Error("Invalid layout: cant swap if only root exists");

      const valA = getLeaf(next, pathA);
      const valB = getLeaf(next, pathB);

      setNode(next, pathA, valB);
      setNode(next, pathB, valA);
      return next;
    });
  };

  const handleSnapback = (parentPathId: string) => {
    const parentPath = parentPathId.split("-").slice(1).map(Number);
    const parentNode = getNode(layout, parentPath);
    if (parentNode.orient === "row") {
      setRowResize([parentPathId, [50, 50]]);
    } else {
      setColumnResize([parentPathId, [50, 50]]);
    }
  };

  return {
    handleResize,
    handleLeaf,
    handleSplit,
    handleMerge,
    handleDelete,
    handleSwap,
    handleSnapback,
  };
};

export default useGridCallbacks;
