(function () {
  if (!Session.getAccessToken()) {
    window.location.replace("/login");
    return;
  }

  const EVENT_LABELS = {
    request_submitted: "Заявка отправлена",
    request_approved: "Заявка согласована",
    request_rejected: "Заявка отклонена",
    request_returned: "Заявка возвращена",
    request_cancelled: "Заявка отменена",
    new_task: "Новая задача",
    status_change: "Изменение статуса",
  };

  const userNameEl = document.getElementById("user-name");
  const logoutBtn = document.getElementById("logout-btn");
  const notifList = document.getElementById("notif-list");
  const stateLoading = document.getElementById("state-loading");
  const stateEmpty = document.getElementById("state-empty");
  const stateError = document.getElementById("state-error");
  const stateErrorMessage = document.getElementById("state-error-message");
  const retryBtn = document.getElementById("retry-btn");

  const user = Session.getUser();
  userNameEl.textContent = (user && user.full_name) || "";

  logoutBtn.addEventListener("click", function () {
    Session.clear();
    window.location.href = "/login";
  });

  retryBtn.addEventListener("click", function () {
    loadNotifications();
  });

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatDateTime(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString("ru-RU");
  }

  function eventLabel(eventType) {
    return EVENT_LABELS[eventType] || eventType || "—";
  }

  function hideAllStates() {
    stateLoading.hidden = true;
    stateEmpty.hidden = true;
    stateError.hidden = true;
    notifList.hidden = true;
  }

  function renderItems(items) {
    notifList.innerHTML = items
      .map(function (item) {
        const type = item.event_type || "";
        const text = item.text || "—";
        const at = formatDateTime(item.created_at);
        const openLink =
          item.request_id != null
            ? '<a class="btn-link notif-open" href="/my-requests/' +
              encodeURIComponent(item.request_id) +
              '">Открыть заявку</a>'
            : "";
        return (
          '<article class="notif-item">' +
          '<div class="notif-item-main">' +
          '<div class="notif-type">' +
          escapeHtml(eventLabel(type)) +
          "</div>" +
          '<div class="notif-text">' +
          escapeHtml(text) +
          "</div>" +
          '<div class="notif-at">' +
          escapeHtml(at) +
          "</div>" +
          "</div>" +
          (openLink ? '<div class="notif-item-actions">' + openLink + "</div>" : "") +
          "</article>"
        );
      })
      .join("");
  }

  async function loadNotifications() {
    hideAllStates();
    stateLoading.hidden = false;

    try {
      const payload = await apiFetch("/notifications");
      const items = (payload && payload.items) || [];
      hideAllStates();
      if (items.length === 0) {
        stateEmpty.hidden = false;
      } else {
        renderItems(items);
        notifList.hidden = false;
      }
    } catch (err) {
      hideAllStates();
      stateErrorMessage.textContent =
        err && err.message
          ? err.message
          : "Произошла внутренняя ошибка. Попробуйте позже";
      stateError.hidden = false;
    }
  }

  loadNotifications();
})();
