/** Session storage for JWT client (ADR-AUTH-JWT-01). */
(function (global) {
  const KEY = "employee_service_session";

  function read() {
    try {
      const raw = sessionStorage.getItem(KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (_err) {
      return null;
    }
  }

  function write(session) {
    sessionStorage.setItem(KEY, JSON.stringify(session));
  }

  function clear() {
    sessionStorage.removeItem(KEY);
  }

  function getAccessToken() {
    const session = read();
    return session && session.access_token ? session.access_token : null;
  }

  function getUser() {
    const session = read();
    return session && session.user ? session.user : null;
  }

  function saveLoginResponse(payload) {
    write({
      access_token: payload.access_token,
      token_type: payload.token_type || "bearer",
      expires_in: payload.expires_in,
      user: payload.user,
    });
  }

  global.Session = {
    KEY,
    read,
    write,
    clear,
    getAccessToken,
    getUser,
    saveLoginResponse,
  };
})(window);
