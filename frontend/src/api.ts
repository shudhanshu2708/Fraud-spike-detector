const API_BASE_URL = "http://127.0.0.1:8000";

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem("access_token");

  const headers = new Headers(options.headers);

  headers.set("Content-Type", "application/json");

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers,
    },
  );

  if (!response.ok) {
    let message = "Request failed";

    try {
      const data = await response.json();
      message =
        typeof data.detail === "string"
          ? data.detail
          : message;
    } catch {
      // Keep default message.
    }

    throw new Error(message);
  }

  return response.json();
}