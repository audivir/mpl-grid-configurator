import { LayoutNode, FigSize } from "./layout";

export const API_BASE = "http://localhost:8765";
export const DEFAULT_DPI = 96;
export const DEFAULT_LAYOUT = {
  orient: "row",
  children: ["draw_empty", "draw_empty"],
  ratios: [50, 50],
} as LayoutNode;
export const DEFAULT_FIGSIZE = [8, 4] as FigSize;
export const RENDER_DEBOUNCE = 150;
export const RESIZE_DEBOUNCE = 50;
export const RESIZE_EPSILON = 0.01;
export const STORAGE_KEYS = {
  LAYOUT: "plot-layout-v1",
  FIGSIZE: "plot-figsize-v1",
  SIDEBAR_PINNED: "plot-sidebar-pinned-v1",
  SESSION_TOKEN: "plot-session-token-v1",
} as const;
