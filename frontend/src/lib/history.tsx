import { useCallback, useReducer } from "react";
import { Layout, FigSize, LayoutNode } from "../lib/layout";

interface HistoryState {
  past: Array<{ layout: Layout; figsize: FigSize }>;
  present: { layout: Layout; figsize: FigSize };
  future: Array<{ layout: Layout; figsize: FigSize }>;
}

type HistoryAction =
  | { type: "UNDO" }
  | { type: "REDO" }
  | { type: "SET"; layout: Layout; figsize: FigSize }
  | { type: "RESET"; layout: Layout; figsize: FigSize };

const historyReducer = (
  state: HistoryState,
  action: HistoryAction
): HistoryState => {
  const { past, present, future } = state;

  switch (action.type) {
    case "UNDO": {
      if (past.length === 0) return state;
      const previous = past[past.length - 1];
      const newPast = past.slice(0, -1);
      console.log(
        "undoing to",
        (previous.layout as LayoutNode).ratios,
        (present.layout as LayoutNode).ratios
      );

      return {
        past: newPast,
        present: previous,
        future: [present, ...future],
      };
    }

    case "REDO": {
      if (future.length === 0) return state;
      const next = future[0];
      const newFuture = future.slice(1);

      return {
        past: [...past, present],
        present: next,
        future: newFuture,
      };
    }

    case "SET": {
      // Don't push to history if nothing changed
      if (
        JSON.stringify(present.layout) === JSON.stringify(action.layout) &&
        present.figsize.w === action.figsize.w &&
        present.figsize.h === action.figsize.h
      ) {
        return state;
      }

      return {
        past: [...past, present].slice(-50), // Limit history to 50 steps
        present: { layout: action.layout, figsize: action.figsize },
        future: [], // New actions clear the redo stack
      };
    }

    case "RESET": {
      return {
        past: [],
        present: { layout: action.layout, figsize: action.figsize },
        future: [],
      };
    }

    default:
      return state;
  }
};

const useHistory = (initialLayout: Layout, initialFigsize: FigSize) => {
  const [state, dispatch] = useReducer(historyReducer, {
    past: [],
    present: { layout: initialLayout, figsize: initialFigsize },
    future: [],
  });

  const canUndo = state.past.length > 0;
  const canRedo = state.future.length > 0;

  const undo = useCallback(() => dispatch({ type: "UNDO" }), []);
  const redo = useCallback(() => dispatch({ type: "REDO" }), []);

  const setPresent = useCallback((layout: Layout, figsize: FigSize) => {
    dispatch({ type: "SET", layout, figsize });
  }, []);

  const resetHistory = useCallback((layout: Layout, figsize: FigSize) => {
    dispatch({ type: "RESET", layout, figsize });
  }, []);

  return {
    state: state.present,
    undo,
    redo,
    setPresent,
    resetHistory,
    canUndo,
    canRedo,
  };
};

export default useHistory;
