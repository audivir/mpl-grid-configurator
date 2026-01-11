import { toast } from "sonner";
import { API_BASE } from "./const";
import { FigSize, Layout, Orientation, RestructureInfo } from "./layout";

// Standard response for layout-modifying operations
export interface FullResponse {
  token: string;
  figsize: FigSize;
  layout: Layout;
  svg: string;
}

interface MergeResponse extends FullResponse {
  inverse: [string, { [key: string]: any }][];
}

const getErrorMessage = async (response: Response): Promise<string> => {
  try {
    const data = await response.json();
    return typeof data.detail === "string"
      ? data.detail
      : data.detail?.[0]?.msg || "Unknown error";
  } catch {
    return `Server Error: ${response.statusText}`;
  }
};

/**
 * Optimized Fetch Wrapper
 */
async function apiRequest<T>(
  endpoint: string,
  method: "GET" | "POST",
  body?: any,
  token?: string | null,
  errorTitle = "Error"
): Promise<T | null> {
  try {
    console.log("API Request", endpoint, method, body, token, errorTitle);
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      ...(body && { body: JSON.stringify(body) }),
    });

    if (!response.ok) {
      const description = await getErrorMessage(response);
      toast.error(errorTitle, { description });
      return null;
    }

    return await response.json();
  } catch (error) {
    toast.error("Network Error", {
      description: "Connection to backend lost.",
    });
    return null;
  }
}

export const api = {
  // Main API
  functions: () =>
    apiRequest<string[]>("/functions", "GET", null, null, "Functions Failed"),

  health: (tok: string | null) =>
    apiRequest<boolean>("/health", "GET", null, tok, "Health Failed"),

  render: (l: Layout, fs: FigSize, tok: string | null) =>
    apiRequest<FullResponse>(
      "/render",
      "POST",
      { layout: l, figsize: fs },
      tok,
      "Render Failed"
    ),

  session: (l: Layout, fs: FigSize) => {
    console.log("Session Request", l, fs);
    return apiRequest<FullResponse>(
      "/session",
      "POST",
      { layout: l, figsize: fs },
      null,
      "Session Failed"
    );
  },

  edit: {
    delete: (path: number[], tok: string | null) =>
      apiRequest<FullResponse>(
        "/edit/delete",
        "POST",
        { path },
        tok,
        "Delete Failed"
      ),

    insert: (
      path: number[],
      orient: Orientation,
      ratios: number[],
      value: string,
      tok: string | null
    ) =>
      apiRequest<FullResponse>(
        "/edit/insert",
        "POST",
        { path, orient, ratios, value },
        tok,
        "Insert Failed"
      ),

    merge: (pathA: number[], pathB: number[], tok: string | null) =>
      apiRequest<MergeResponse>(
        "/edit/merge",
        "POST",
        { pathA, pathB },
        tok,
        "Merge Failed"
      ),

    replace: (path: number[], value: string, tok: string | null) =>
      apiRequest<FullResponse>(
        "/edit/replace",
        "POST",
        { path, value },
        tok,
        "Replace Failed"
      ),

    resize: (fs: FigSize, tok: string | null) =>
      apiRequest<FullResponse>(
        "/edit/resize",
        "POST",
        { figsize: fs },
        tok,
        "Resize Failed"
      ),

    restructure: (
      r: RestructureInfo | null,
      c: RestructureInfo | null,
      tok: string | null
    ) =>
      apiRequest<FullResponse>(
        "/edit/restructure",
        "POST",
        { rowRestructureInfo: r, columnRestructureInfo: c },
        tok,
        "Restructure Failed"
      ),

    rotate: (path: number[], tok: string | null) =>
      apiRequest<FullResponse>(
        "/edit/rotate",
        "POST",
        { path },
        tok,
        "Rotate Failed"
      ),

    split: (path: number[], orient: Orientation, tok: string | null) =>
      apiRequest<FullResponse>(
        "/edit/split",
        "POST",
        { path, orient },
        tok,
        "Split Failed"
      ),

    swap: (pathA: number[], pathB: number[], tok: string | null) =>
      apiRequest<FullResponse>(
        "/edit/swap",
        "POST",
        { pathA, pathB },
        tok,
        "Swap Failed"
      ),

    unmerge: (
      inverse: [string, { [key: string]: any }][],
      tok: string | null
    ) =>
      apiRequest<FullResponse>(
        "/edit/unmerge",
        "POST",
        { inverse },
        tok,
        "Unmerge Failed"
      ),
  },
};
