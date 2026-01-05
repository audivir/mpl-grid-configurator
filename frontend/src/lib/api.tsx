import { toast } from "sonner";
import { API_BASE } from "./const";

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
  errorTitle = "Request Failed"
): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
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
  getFunctions: () => apiFetch<string[]>("/functions", { method: "GET" }),

  render: (layout: any, figsize: [number, number]) =>
    apiFetch<{ svg: string }>(
      "/render",
      {
        method: "POST",
        body: JSON.stringify({ layout, figsize }),
      },
      "Render Failed"
    ),

  merge: (layoutData: any, pathA: number[], pathB: number[]) =>
    apiFetch<{ layout: any; svg: string }>(
      "/merge",
      {
        method: "POST",
        body: JSON.stringify({
          layout_data: layoutData,
          path_a: pathA,
          path_b: pathB,
        }),
      },
      "Merge Failed"
    ),
};
