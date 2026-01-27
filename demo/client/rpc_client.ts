import { RpcError } from "./rpc_types.js";

export interface RpcCallOptions {
  method: string;
  // JSON-serializable params object for the RPC method.
  params: object;
  timeoutMs?: number;
}

const DEFAULT_TIMEOUT_MS = 10_000;

export class RpcClient {
  private apiUrl: string;

  constructor(apiUrl: string) {
    this.apiUrl = apiUrl;
  }

  async call<T>(options: RpcCallOptions): Promise<T> {
    // Extract request options and apply a default timeout if not provided.
    const { method, params, timeoutMs = DEFAULT_TIMEOUT_MS } = options;

    // Use AbortController so we can time out the request cleanly.
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    // Send the RPC request. All methods are POSTed to /api with { method, params }.
    const res = await fetch(this.apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method, params }),
      signal: controller.signal,
    });

    // Clear the timeout once the request completes.
    clearTimeout(timeoutId);

    // Parse the JSON response body.
    const data = await res.json();

    // If the HTTP response is not OK, or the RPC response indicates an error,
    // convert it into a thrown Error with a stable code and optional details.
    if (!res.ok || data.status === "error") {
      const err: RpcError | undefined = data?.error;
      const code = err?.code ?? "RPC_ERROR";
      const message = err?.message ?? `RPC call failed (${res.status})`;
      const details = err?.details;
      const error = new Error(`${code}: ${message}`);
      if (details) {
        (error as Error & { details?: unknown }).details = details;
      }
      throw error;
    }

    // Successful response: return the parsed data as the expected type.
    return data as T;
  }
}
