(function () {
  if (Session.getAccessToken()) {
    window.location.replace("/my-requests");
    return;
  }

  const form = document.getElementById("login-form");
  const submitBtn = document.getElementById("login-submit");
  const errorEl = document.getElementById("login-error");
  const loginInput = document.getElementById("login");
  const passwordInput = document.getElementById("password");

  const DEFAULT_LABEL = "Войти";
  const LOADING_LABEL = "Вход…";

  function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    submitBtn.textContent = isLoading ? LOADING_LABEL : DEFAULT_LABEL;
    loginInput.disabled = isLoading;
    passwordInput.disabled = isLoading;
  }

  function showError(message) {
    errorEl.hidden = false;
    errorEl.textContent = message;
  }

  function clearError() {
    errorEl.hidden = true;
    errorEl.textContent = "";
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    clearError();
    setLoading(true);

    try {
      const payload = await apiFetch("/auth/login", {
        method: "POST",
        auth: false,
        redirectOnUnauthorized: false,
        body: {
          login: loginInput.value.trim(),
          password: passwordInput.value,
        },
      });
      Session.saveLoginResponse(payload);
      window.location.href = "/my-requests";
    } catch (err) {
      const message =
        err && err.message
          ? err.message
          : "Произошла внутренняя ошибка. Попробуйте позже";
      showError(message);
      setLoading(false);
    }
  });
})();
