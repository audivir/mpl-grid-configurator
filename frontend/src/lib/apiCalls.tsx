import { api, FullResponse } from "./api";
import {
  Layout,
  LPath,
  FigureSize,
  RestructureInfo,
  Ratios,
  Orient,
  getNode,
  getLeaf,
} from "./layout";

export type ApiCall<T> = {
  do: () => Promise<T>;
  undo: () => Promise<T>;
};

export const apiCalls = {
  delete: (
    layout: Layout,
    path: LPath,
    sessionToken: string | null
  ): ApiCall<FullResponse | null> => {
    const parentPath = path.slice(0, -1);
    const parent = getNode(layout, parentPath);
    const orient = parent.orient;
    const ratios = parent.ratios;
    const leaf = getLeaf(parent, path.slice(-1));
    return {
      do: async () => api.edit.delete(path, sessionToken),
      undo: async () =>
        api.edit.insert(path, orient, ratios, leaf, sessionToken),
    };
  },

  insert: (
    path: LPath,
    orient: Orient,
    ratios: Ratios,
    value: string,
    sessionToken: string | null
  ): ApiCall<FullResponse | null> => {
    return {
      do: async () =>
        api.edit.insert(path, orient, ratios, value, sessionToken),
      undo: async () => api.edit.delete(path, sessionToken),
    };
  },

  merge: (
    pathA: LPath,
    pathB: LPath,
    sessionToken: string | null
  ): ApiCall<FullResponse | null> => {
    let undoData: [string, { [key: string]: any }][] | null = null;
    return {
      do: async () => {
        const res = await api.edit.merge(pathA, pathB, sessionToken);
        if (!res) {
          return null;
        }
        undoData = res.inverse;
        return {
          token: res.token,
          figsize: res.figsize,
          layout: res.layout,
          svg: res.svg,
        } as FullResponse;
      },
      undo: async () => {
        if (!undoData) {
          console.error("Merge's do() not called or failed. Cannot undo.");
          return null;
        }
        return api.edit.unmerge(undoData, sessionToken);
      },
    };
  },

  replace: (
    layout: Layout,
    path: LPath,
    value: string,
    sessionToken: string | null
  ): ApiCall<FullResponse | null> => {
    const leaf = getLeaf(layout, path);
    return {
      do: async () => api.edit.replace(path, value, sessionToken),
      undo: async () => api.edit.replace(path, leaf, sessionToken),
    };
  },

  resize: (
    figsize: FigureSize,
    newFigsize: FigureSize,
    sessionToken: string | null
  ): ApiCall<FullResponse | null> => {
    return {
      do: async () => api.edit.resize(newFigsize, sessionToken),
      undo: async () => api.edit.resize(figsize, sessionToken),
    };
  },

  restructure: (
    layout: Layout,
    rowRestructureInfo: RestructureInfo | null,
    columnRestructureInfo: RestructureInfo | null,
    sessionToken: string | null
  ): ApiCall<FullResponse | null> => {
    let prevRowRestructureInfo: RestructureInfo | null = null;
    let prevColumnRestructureInfo: RestructureInfo | null = null;
    if (rowRestructureInfo) {
      const rowParentPath = rowRestructureInfo[0];
      const prevRowNode = getNode(layout, rowParentPath);
      const prevRatios = prevRowNode.ratios;
      prevRowRestructureInfo = [rowParentPath, prevRatios];
    }
    if (columnRestructureInfo) {
      const columnParentPath = columnRestructureInfo[0];
      const prevColumnNode = getNode(layout, columnParentPath);
      const prevRatios = prevColumnNode.ratios;
      prevColumnRestructureInfo = [columnParentPath, prevRatios];
    }

    return {
      do: async () =>
        api.edit.restructure(
          rowRestructureInfo,
          columnRestructureInfo,
          sessionToken
        ),
      undo: async () =>
        api.edit.restructure(
          prevRowRestructureInfo,
          prevColumnRestructureInfo,
          sessionToken
        ),
    };
  },

  rotate: (
    path: LPath,
    sessionToken: string | null
  ): ApiCall<FullResponse | null> => {
    return {
      do: async () => api.edit.rotate(path, sessionToken),
      undo: async () => api.edit.rotate(path, sessionToken),
    };
  },

  split: (
    path: LPath,
    orient: Orient,
    sessionToken: string | null
  ): ApiCall<FullResponse | null> => {
    return {
      do: async () => api.edit.split(path, orient, sessionToken),
      undo: async () => api.edit.delete([...path, 1], sessionToken),
    };
  },

  swap: (
    pathA: LPath,
    pathB: LPath,
    sessionToken: string | null
  ): ApiCall<FullResponse | null> => {
    return {
      do: async () => api.edit.swap(pathA, pathB, sessionToken),
      undo: async () => api.edit.swap(pathB, pathA, sessionToken),
    };
  },

  render: (
    layout: Layout,
    figsize: FigureSize,
    sessionToken: string | null
  ): ApiCall<FullResponse | null> => {
    return {
      do: async () => api.render(layout, figsize, sessionToken),
      undo: async () => null,
    };
  },
};
