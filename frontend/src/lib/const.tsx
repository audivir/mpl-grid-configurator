import { ParseOptions } from "jsonc-parser";
import { LayoutNode, FigureSize, Ratios, Orient } from "./layout";

export const API_BASE = "http://localhost:8765";
export const DEFAULT_ORIENT = "row" as Orient;
export const DEFAULT_LEAF = "draw_empty";
export const DEFAULT_RATIOS = [50, 50] as Ratios;
export const DEFAULT_LAYOUT = {
  orient: DEFAULT_ORIENT,
  children: [DEFAULT_LEAF, DEFAULT_LEAF],
  ratios: DEFAULT_RATIOS,
} as LayoutNode;
export const DEFAULT_DPI = 96;
export const DEFAULT_FIGSIZE = [8, 4] as FigureSize;
export const RESIZE_DEBOUNCE = 50;
export const RESIZE_EPSILON = 0.01;
export const STORAGE_KEYS = {
  LAYOUT: "plot-layout-v1",
  FIGSIZE: "plot-figsize-v1",
  SIDEBAR_PINNED: "plot-sidebar-pinned-v1",
  SESSION_TOKEN: "plot-session-token-v1",
} as const;
export const JSON_PARSE_OPTIONS = {
  disallowComments: false,
  allowTrailingComma: true,
  allowEmptyContent: true,
} as ParseOptions;
