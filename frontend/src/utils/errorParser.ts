import axios from 'axios';

/**
 * Parsed error details from API responses or other exceptions.
 * Safely extracts validation messages, server errors, and network anomalies
 * to prevent rendering crashes in React components.
 */
export function parseApiError(err: unknown): string {
  if (!err) {
    return 'An unknown error occurred.';
  }

  // Check if it is an Axios error
  if (axios.isAxiosError(err)) {
    const response = err.response;

    // 1. If server responded with a status outside the 2xx range
    if (response) {
      const data = response.data;
      const status = response.status;

      // Handle server-side crashes / unexpected internal errors (HTTP 500+)
      if (status >= 500) {
        return 'Server error: An unexpected error occurred on the server. Please try again later.';
      }

      // Process standard error response payloads
      if (data && typeof data === 'object') {
        const detail = (data as any).detail;

        if (detail !== undefined && detail !== null) {
          // Case 1: detail is a direct error string
          if (typeof detail === 'string') {
            return detail;
          }

          // Case 2: detail is a FastAPI pydantic validation error array
          if (Array.isArray(detail)) {
            const messages = detail.map((item: any) => {
              if (item && typeof item === 'object') {
                return item.msg || item.message || JSON.stringify(item);
              }
              if (typeof item === 'string') {
                return item;
              }
              return JSON.stringify(item);
            });
            return messages.filter(Boolean).join(', ');
          }

          // Case 3: detail is an object (unexpected structured error)
          if (typeof detail === 'object') {
            const detailObj = detail as any;
            return detailObj.msg || detailObj.message || JSON.stringify(detail);
          }
        }

        // Fallbacks for other structures e.g. { message: "..." } or { error: "..." }
        const fallbackMsg = (data as any).message || (data as any).error;
        if (typeof fallbackMsg === 'string') {
          return fallbackMsg;
        }
      }

      // If data is a string
      if (data && typeof data === 'string') {
        return data;
      }
    } else if (err.request) {
      // 2. Request was made but no response was received (e.g. Network error)
      return 'Network error: Please check your internet connection and try again.';
    }
  }

  // Handle standard JavaScript Error objects
  if (err instanceof Error) {
    return err.message;
  }

  // Handle plain string error throws
  if (typeof err === 'string') {
    return err;
  }

  // Fallback stringification
  try {
    return JSON.stringify(err);
  } catch {
    return 'An unexpected error occurred.';
  }
}
