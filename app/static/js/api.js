/** Thin fetch wrapper for Core API (flat error envelope Pre-E2 runtime). */
(function (global) {
  class ApiError extends Error {
    constructor(status, errorCode, message, details) {
      super(message || "Request failed");
      this.name = "ApiError";
      this.status = status;
      this.errorCode = errorCode || null;
      this.details = details || {};
    }
  }

  async function parseBody(response) {
    const text = await response.text();
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (_err) {
      return { message: text };
    }
  }

  function extractError(body) {
    if (!body || typeof body !== "object") {
      return { errorCode: null, message: null, details: {} };
    }
    // Pre-E2 / current runtime: flat { error_code, message, details }
    if (body.error_code) {
      return {
        errorCode: body.error_code,
        message: body.message || null,
        details: body.details || {},
      };
    }
    // Target nested envelope (if present)
    if (body.error && typeof body.error === "object") {
      return {
        errorCode: body.error.code || null,
        message: body.error.message || null,
        details: body.error.details || {},
      };
    }
    return { errorCode: null, message: body.message || null, details: {} };
  }

  async function apiFetch(path, options) {
    const opts = options || {};
    const headers = Object.assign({ Accept: "application/json" }, opts.headers || {});
    const auth = opts.auth !== false;
    if (auth) {
      const token = global.Session && Session.getAccessToken();
      if (token) {
        headers.Authorization = "Bearer " + token;
      }
    }
    if (opts.body != null && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    let response;
    try {
      response = await fetch(path, {
        method: opts.method || "GET",
        headers,
        body: opts.body != null ? JSON.stringify(opts.body) : undefined,
      });
    } catch (_networkErr) {
      throw new ApiError(
        0,
        "ERR_NETWORK",
        "Произошла внутренняя ошибка. Попробуйте позже",
        {}
      );
    }

    const body = await parseBody(response);

    if (response.status === 401 && auth) {
      if (global.Session) Session.clear();
      if (opts.redirectOnUnauthorized !== false) {
        window.location.href = "/login";
      }
    }

    if (!response.ok) {
      const err = extractError(body);
      const fallback =
        response.status >= 500
          ? "Произошла внутренняя ошибка. Попробуйте позже"
          : "Запрос не выполнен";
      throw new ApiError(
        response.status,
        err.errorCode,
        err.message || fallback,
        err.details
      );
    }

    if (response.status === 204) return null;
    return body;
  }

  global.ApiError = ApiError;
  global.apiFetch = apiFetch;
})(window);
