import { z } from "zod";

export type LPath = number[];
export type Ratios = [number, number];
export type RestructuredLayout = import("react-resizable-panels").Layout;
export type Resize = [string, Ratios] | null;
export type RestructureInfo = [LPath, Ratios] | null;

const OrientSchema = z.enum(["row", "column"]);
export type Orient = z.infer<typeof OrientSchema>;
export type LayoutNode = {
  orient: Orient;
  children: [Layout, Layout];
  ratios: Ratios;
};
export type Layout = string | LayoutNode;
const LayoutNodeSchema: z.ZodType<LayoutNode> = z.lazy(() =>
  z.object({
    orient: OrientSchema,
    children: z.tuple([LayoutSchema, LayoutSchema]),
    ratios: z.tuple([z.number(), z.number()]),
  })
);
const LayoutSchema: z.ZodType<Layout> = z.lazy(() =>
  z.union([LayoutNodeSchema, z.string()])
);

const FigureSizeSchema = z.tuple([z.number(), z.number()]);
export type FigureSize = z.infer<typeof FigureSizeSchema>;

export const ConfigSchema = z.object({
  layout: LayoutSchema,
  figsize: FigureSizeSchema,
});

export type Config = z.infer<typeof ConfigSchema>;

/**
 * Get the leaf or node at the given path.
 */
export const getAt = (layout: Layout, path: LPath) => {
  if (path.length === 0) return layout;
  if (typeof layout !== "object")
    throw new Error("Invalid path: must be object if path is not empty");
  let target = layout as Layout;
  for (let i = 0; i < path.length; i++) {
    if (typeof target !== "object")
      throw new Error("Invalid path: must be object if not at end");
    target = target.children[path[i]];
  }
  return target;
};

/**
 * Get the node at the given path.
 */
export const getNode = (layout: Layout, path: LPath) => {
  const target = getAt(layout, path);
  if (typeof target !== "object")
    throw new Error("Invalid path: must be object at end");
  return target;
};

/**
 * Get the leaf at the given path.
 */
export const getLeaf = (layout: Layout, path: LPath) => {
  const target = getAt(layout, path);
  if (typeof target !== "string")
    throw new Error("Invalid path: must be string at end");
  return target;
};

/**
 * Set the node at the given path.
 */
export const setNode = (layout: LayoutNode, path: LPath, val: Layout) => {
  if (typeof layout === "string")
    throw new Error("Invalid layout: cant set at string");
  if (path.length === 0)
    throw new Error("Invalid path: path must be non-empty");
  let target = layout;
  for (let i = 0; i < path.length - 1; i++) {
    let child = target.children[path[i]];
    if (typeof child === "string")
      throw new Error("Invalid path: must be object every step");
    target = child;
  }
  target.children[path[path.length - 1]] = val;
};
