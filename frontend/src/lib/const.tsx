import { Layout, FigSize } from "./layout";

export const API_BASE = "http://localhost:8765";
export const DEFAULT_DPI = 96;
export const DEFAULT_LAYOUT = "draw_empty" as Layout;
export const DEFAULT_FIGSIZE = { w: 8, h: 4 } as FigSize;
export const RESIZE_DEBOUNCE = 50;
export const RENDER_DEBOUNCE = 150;
export const STORAGE_KEYS = {
  LAYOUT: "plot-layout-v1",
  FIGSIZE: "plot-figsize-v1",
} as const;
