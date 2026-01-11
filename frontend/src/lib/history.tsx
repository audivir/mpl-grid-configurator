import { useCallback, useReducer } from "react";
import { FullResponse } from "../lib/api";
import { Layout, FigSize } from "../lib/layout";
import { ApiCall } from "./apiCalls";

export type HistoryActionType =
  | "DELETE"
  | "INSERT"
  | "MERGE"
  | "REPLACE"
  | "RESIZE"
  | "RESTRUCTURE"
  | "ROTATE"
  | "SPLIT"
  | "SWAP";

interface HistoryDelta {
  type: HistoryActionType;
  call: ApiCall<FullResponse | null>;
}

interface HistoryState {
  past: HistoryDelta[];
  present: { layout: Layout; figsize: FigSize };
  future: HistoryDelta[];
}

type HistoryAction =
  | {
      type: "PUSH";
      actionType: HistoryActionType;
      call: ApiCall<FullResponse | null>;
      layout: Layout;
      figsize: FigSize;
    }
  | { type: "UNDO"; layout: Layout; figsize: FigSize }
  | { type: "REDO"; layout: Layout; figsize: FigSize }
  | { type: "SET"; layout: Layout; figsize: FigSize }
  | { type: "RESET"; layout: Layout; figsize: FigSize };

const historyReducer = (
  state: HistoryState,
  action: HistoryAction
): HistoryState => {
  switch (action.type) {
    case "PUSH":
      //     if (
      //   state.past.length > 0 &&
      //   JSON.stringify(state.past[state.past.length - 1]) ===
      //     JSON.stringify(action.delta)
      // )
      //   return state;
      return {
        past: [
          ...state.past,
          { type: action.actionType, call: action.call },
        ].slice(-50),
        present: { layout: action.layout, figsize: action.figsize },
        future: [],
      };
    case "UNDO":
      const undoDelta = state.past[state.past.length - 1];
      return {
        past: state.past.slice(0, -1),
        present: { layout: action.layout, figsize: action.figsize },
        future: [undoDelta, ...state.future],
      };
    case "REDO":
      const redoDelta = state.future[0];
      return {
        past: [...state.past, redoDelta],
        present: { layout: action.layout, figsize: action.figsize },
        future: state.future.slice(1),
      };
    case "SET":
    case "RESET":
      return {
        past: action.type === "RESET" ? [] : state.past,
        present: { layout: action.layout, figsize: action.figsize },
        future: action.type === "RESET" ? [] : state.future,
      };
    default:
      return state;
  }
};

interface UseHistoryProps {
  initialLayout: Layout;
  initialFigsize: FigSize;
}

export type History = {
  state: { layout: Layout; figsize: FigSize };
  undo: () => Promise<FullResponse | null>;
  redo: () => Promise<FullResponse | null>;
  executeAction: (
    type: HistoryActionType,
    apiCallBuilder: (l: Layout, f: FigSize) => ApiCall<FullResponse | null>
  ) => Promise<FullResponse | null>;
  setPresent: (layout: Layout, figsize: FigSize) => void;
  reset: (layout: Layout, figsize: FigSize) => void;
  canUndo: boolean;
  canRedo: boolean;
};

const useHistory = ({
  initialLayout,
  initialFigsize,
}: UseHistoryProps): History => {
  const [state, dispatch] = useReducer(historyReducer, {
    past: [],
    present: { layout: initialLayout, figsize: initialFigsize },
    future: [],
  });

  const setPresent = (layout: Layout, figsize: FigSize) =>
    dispatch({ type: "SET", layout, figsize });

  const executeAction = async (
    type: HistoryActionType,
    apiCallBuilder: (l: Layout, f: FigSize) => ApiCall<FullResponse | null>
  ) => {
    const apiCall = apiCallBuilder(state.present.layout, state.present.figsize);
    const res = await apiCall.do();
    if (res) {
      dispatch({
        type: "PUSH",
        actionType: type,
        call: apiCall,
        layout: res.layout,
        figsize: res.figsize,
      });
      return res;
    }
    return null;
  };

  const undo = async () => {
    if (state.past.length === 0) return null;
    const delta = state.past[state.past.length - 1];
    const res = await delta.call.undo();
    if (res) {
      dispatch({ type: "UNDO", layout: res.layout, figsize: res.figsize });
    }
    return res;
  };

  const redo = async () => {
    if (state.future.length === 0) return null;
    const delta = state.future[0];
    const res = await delta.call.do();
    if (res) {
      dispatch({ type: "REDO", layout: res.layout, figsize: res.figsize });
    }
    return res;
  };

  const reset = useCallback(() => {
    dispatch({ type: "RESET", layout: initialLayout, figsize: initialFigsize });
  }, [initialLayout, initialFigsize]);

  return {
    state: state.present,
    undo,
    redo,
    executeAction,
    setPresent,
    reset,
    canUndo: state.past.length > 0,
    canRedo: state.future.length > 0,
  };
};

export default useHistory;
