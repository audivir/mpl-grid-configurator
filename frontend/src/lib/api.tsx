import { toast } from "sonner";
import { API_BASE } from "./const";
import { FigSize, Layout } from "./layout";

/**
 * Parses FastAPI error details
 */
const getErrorMessage = async (response: Response): Promise<string> => {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return data.detail[0].msg;
    return "An unexpected error occurred.";
  } catch {
    return `Server Error: ${response.statusText}`;
  }
};

/**
 * Backend API wrapper with forwarding errors to toast
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  sessionToken: string | null = null,
  errorTitle = "Request Failed"
): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
        Authorization: sessionToken ? `Bearer ${sessionToken}` : "",
      },
    });

    if (!response.ok) {
      const detail = await getErrorMessage(response);
      toast.error(errorTitle, { description: detail });
      return null;
    }

    return await response.json();
  } catch (error) {
    toast.error("Network Error", {
      description: "Could not connect to the backend server.",
    });
    return null;
  }
}

/**
 * API calls to backend
 */
export const api = {
  healthCheck: (tok: string | null) =>
    apiFetch<boolean>("/health", { method: "GET" }, tok, "Health Check Failed"),

  createSession: (l: Layout, fs: FigSize) =>
    apiFetch<{ token: string; svg: string }>("/session", {
      method: "POST",
      body: JSON.stringify({ layout: l, figsize: [fs.w, fs.h] }),
    }),

  getFunctions: () => apiFetch<string[]>("/functions", { method: "GET" }),

  render: (l: Layout, fs: FigSize, tok: string | null) =>
    apiFetch<{ token: string; svg: string }>(
      "/render",
      {
        method: "POST",
        body: JSON.stringify({ layout: l, figsize: [fs.w, fs.h] }),
      },
      tok,
      "Render Failed"
    ),

  merge: (
    l: Layout,
    fs: FigSize,
    pA: number[],
    pB: number[],
    tok: string | null
  ) =>
    apiFetch<{ token: string; layout: Layout; svg: string }>(
      "/merge",
      {
        method: "POST",
        body: JSON.stringify({
          layout_data: { layout: l, figsize: [fs.w, fs.h] },
          path_a: pA,
          path_b: pB,
        }),
      },
      tok,
      "Merge Failed"
    ),
};
