export type Orientation = "row" | "column";
export type Resize = [string, [number, number]] | null;
export type LayoutNode = {
  orient: Orientation;
  children: [Layout, Layout];
  ratios: [number, number];
};
export type Layout = string | LayoutNode;

export interface FigSize {
  w: number;
  h: number;
}

/**
 * Get the layout at the given path.
 */
export const getAt = (layout: Layout, path: number[]) => {
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
export const getNode = (layout: Layout, path: number[]) => {
  const target = getAt(layout, path);
  if (typeof target !== "object")
    throw new Error("Invalid path: must be object at end");
  return target;
};

/**
 * Get the leaf at the given path.
 */
export const getLeaf = (layout: Layout, path: number[]) => {
  const target = getAt(layout, path);
  if (typeof target !== "string")
    throw new Error("Invalid path: must be string at end");
  return target;
};

/**
 * Set the node at the given path.
 */
export const setNode = (layout: LayoutNode, path: number[], val: Layout) => {
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
