(function () {
  if (!Session.getAccessToken()) {
    window.location.replace("/login");
    return;
  }

  const STATUS_LABELS = {
    draft: "Черновик",
    in_approval: "На согласовании",
    returned: "Возвращена на доработку",
    approved: "Согласована",
    rejected: "Отклонена",
    cancelled: "Отменена",
  };

  const userNameEl = document.getElementById("user-name");
  const logoutBtn = document.getElementById("logout-btn");
  const createBtn = document.getElementById("create-btn");
  const filtersEl = document.getElementById("filters");
  const tbody = document.getElementById("requests-tbody");
  const tableWrap = document.getElementById("table-wrap");
  const stateLoading = document.getElementById("state-loading");
  const stateEmpty = document.getElementById("state-empty");
  const stateFilterEmpty = document.getElementById("state-filter-empty");
  const stateError = document.getElementById("state-error");
  const stateErrorMessage = document.getElementById("state-error-message");
  const retryBtn = document.getElementById("retry-btn");

  const user = Session.getUser();
  userNameEl.textContent = (user && user.full_name) || "";

  let currentStatus = "";
  let loading = false;

  logoutBtn.addEventListener("click", function () {
    Session.clear();
    window.location.href = "/login";
  });

  // Shown on mockup; next screens are out of this slice scope.
  createBtn.addEventListener("click", function (event) {
    event.preventDefault();
  });

  filtersEl.addEventListener("click", function (event) {
    const chip = event.target.closest(".chip");
    if (!chip || loading) return;
    currentStatus = chip.getAttribute("data-status") || "";
    Array.prototype.forEach.call(filtersEl.querySelectorAll(".chip"), function (el) {
      el.classList.toggle("is-active", el === chip);
    });
    loadRequests();
  });

  retryBtn.addEventListener("click", function () {
    loadRequests();
  });

  function hideAllStates() {
    stateLoading.hidden = true;
    stateEmpty.hidden = true;
    stateFilterEmpty.hidden = true;
    stateError.hidden = true;
    tableWrap.hidden = true;
  }

  function setFiltersDisabled(disabled) {
    Array.prototype.forEach.call(filtersEl.querySelectorAll(".chip"), function (el) {
      el.disabled = disabled;
    });
  }

  function formatDate(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleDateString("ru-RU");
  }

  function statusCode(status) {
    if (!status) return "";
    if (typeof status === "string") return status;
    return status.code || "";
  }

  function statusLabel(status) {
    if (status && typeof status === "object" && status.name) return status.name;
    const code = statusCode(status);
    return STATUS_LABELS[code] || code || "—";
  }

  function statusBadge(status) {
    const code = statusCode(status) || "draft";
    const label = statusLabel(status);
    return '<span class="' + "badge badge-" + escapeHtml(code) + '">' + escapeHtml(label) + "</span>";
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderRows(items) {
    tbody.innerHTML = items
      .map(function (item) {
        const typeName =
          item.request_type && item.request_type.name ? item.request_type.name : "—";
        return (
          "<tr>" +
          "<td>" +
          escapeHtml(typeName) +
          "</td>" +
          "<td>" +
          escapeHtml(formatDate(item.created_at)) +
          "</td>" +
          "<td>" +
          statusBadge(item.status) +
          "</td>" +
          '<td><button type="button" class="btn-link open-btn" data-id="' +
          escapeHtml(item.id) +
          '">Открыть</button></td>' +
          "</tr>"
        );
      })
      .join("");

    Array.prototype.forEach.call(tbody.querySelectorAll(".open-btn"), function (btn) {
      btn.addEventListener("click", function (event) {
        event.preventDefault();
        const id = btn.getAttribute("data-id");
        if (id) {
          window.location.href = "/my-requests/" + encodeURIComponent(id);
        }
      });
    });
  }

  async function loadRequests() {
    loading = true;
    setFiltersDisabled(true);
    hideAllStates();
    stateLoading.hidden = false;

    const query = currentStatus ? "?status=" + encodeURIComponent(currentStatus) : "";

    try {
      const items = await apiFetch("/requests" + query);
      hideAllStates();
      if (!items || items.length === 0) {
        if (currentStatus) {
          stateFilterEmpty.hidden = false;
        } else {
          stateEmpty.hidden = false;
        }
      } else {
        renderRows(items);
        tableWrap.hidden = false;
      }
    } catch (err) {
      hideAllStates();
      stateErrorMessage.textContent =
        err && err.message
          ? err.message
          : "Произошла внутренняя ошибка. Попробуйте позже";
      stateError.hidden = false;
    } finally {
      loading = false;
      setFiltersDisabled(false);
    }
  }

  loadRequests();
})();
