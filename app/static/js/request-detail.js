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

  const COMMENT_REQUIRED = { reject: true, return: true };

  const pathMatch = window.location.pathname.match(/^\/requests\/(\d+)\/?$/);
  const requestId = pathMatch ? pathMatch[1] : null;

  const userNameEl = document.getElementById("user-name");
  const logoutBtn = document.getElementById("logout-btn");
  const detailTitle = document.getElementById("detail-title");
  const detailStatus = document.getElementById("detail-status");
  const detailMeta = document.getElementById("detail-meta");
  const detailValues = document.getElementById("detail-values");
  const detailActions = document.getElementById("detail-actions");
  const detailHistory = document.getElementById("detail-history");
  const detailContent = document.getElementById("detail-content");
  const stateLoading = document.getElementById("state-loading");
  const stateError = document.getElementById("state-error");
  const stateErrorMessage = document.getElementById("state-error-message");
  const actionError = document.getElementById("action-error");
  const commentPanel = document.getElementById("action-comment-panel");
  const commentInput = document.getElementById("action-comment-input");
  const commentConfirm = document.getElementById("action-comment-confirm");
  const commentCancel = document.getElementById("action-comment-cancel");
  const editValuesBtn = document.getElementById("edit-values-btn");
  const deferredEditBanner = document.getElementById("deferred-edit-banner");

  const user = Session.getUser();
  userNameEl.textContent = (user && user.full_name) || "";

  let actionBusy = false;
  let pendingCommentAction = null;
  let fieldNameByCode = {};

  logoutBtn.addEventListener("click", function () {
    Session.clear();
    window.location.href = "/login";
  });

  commentCancel.addEventListener("click", function () {
    hideCommentPanel();
    clearActionError();
  });

  commentConfirm.addEventListener("click", function () {
    if (!pendingCommentAction || actionBusy) return;
    const comment = (commentInput.value || "").trim();
    if (!comment) {
      showActionError("Комментарий обязателен для этого действия");
      return;
    }
    executeAction(pendingCommentAction.id, pendingCommentAction.code, comment);
  });

  editValuesBtn.addEventListener("click", function () {
    deferredEditBanner.hidden = false;
  });

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
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
    return '<span class="badge badge-' + escapeHtml(code) + '">' + escapeHtml(label) + "</span>";
  }

  function formatDateTime(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString("ru-RU");
  }

  function showPageError(message) {
    stateLoading.hidden = true;
    detailContent.hidden = true;
    editValuesBtn.hidden = true;
    deferredEditBanner.hidden = true;
    stateErrorMessage.textContent = message || "Произошла внутренняя ошибка. Попробуйте позже";
    stateError.hidden = false;
  }

  function clearActionError() {
    actionError.hidden = true;
    actionError.textContent = "";
  }

  function showActionError(message) {
    actionError.textContent = message || "Запрос не выполнен";
    actionError.hidden = false;
  }

  function hideCommentPanel() {
    pendingCommentAction = null;
    commentInput.value = "";
    commentPanel.hidden = true;
  }

  function showCommentPanel(action) {
    pendingCommentAction = action;
    commentInput.value = "";
    commentPanel.hidden = false;
    commentInput.focus();
  }

  function setActionsDisabled(disabled) {
    Array.prototype.forEach.call(detailActions.querySelectorAll(".action-chip"), function (btn) {
      btn.disabled = disabled;
    });
    commentConfirm.disabled = disabled;
    commentCancel.disabled = disabled;
    commentInput.disabled = disabled;
  }

  function updateEditControls(card) {
    const isDraft = statusCode(card.status) === "draft";
    editValuesBtn.hidden = !isDraft;
    if (!isDraft) {
      deferredEditBanner.hidden = true;
    }
  }

  function renderMeta(card) {
    const typeName =
      card.request_type && card.request_type.name ? card.request_type.name : "—";
    const typeCode =
      card.request_type && card.request_type.code ? card.request_type.code : "";
    const initiator =
      card.initiator && card.initiator.full_name ? card.initiator.full_name : "—";
    const stage =
      card.current_stage && card.current_stage.name
        ? card.current_stage.name +
          (card.current_stage.sequence_no != null
            ? " (№" + card.current_stage.sequence_no + ")"
            : "")
        : "—";

    detailTitle.textContent = typeName + " №" + card.id;
    detailStatus.innerHTML = statusBadge(card.status);

    detailMeta.innerHTML =
      "<div><dt>Номер</dt><dd>" +
      escapeHtml(card.id) +
      "</dd></div>" +
      "<div><dt>Тип</dt><dd>" +
      escapeHtml(typeName) +
      (typeCode ? ' <span class="meta-code">(' + escapeHtml(typeCode) + ")</span>" : "") +
      "</dd></div>" +
      "<div><dt>Инициатор</dt><dd>" +
      escapeHtml(initiator) +
      "</dd></div>" +
      "<div><dt>Текущий этап</dt><dd>" +
      escapeHtml(stage) +
      "</dd></div>" +
      "<div><dt>Создана</dt><dd>" +
      escapeHtml(formatDateTime(card.created_at)) +
      "</dd></div>" +
      "<div><dt>Обновлена</dt><dd>" +
      escapeHtml(formatDateTime(card.updated_at)) +
      "</dd></div>";
  }

  function fieldLabel(fieldCode) {
    if (fieldCode && fieldNameByCode[fieldCode]) return fieldNameByCode[fieldCode];
    return fieldCode || "—";
  }

  function renderValues(values) {
    if (!values || values.length === 0) {
      detailValues.innerHTML = '<p class="detail-empty">Поля пока не заполнены.</p>';
      return;
    }
    detailValues.innerHTML =
      '<dl class="detail-values">' +
      values
        .map(function (row) {
          const code = row.field_code || "—";
          const value = row.value == null || row.value === "" ? "—" : row.value;
          return (
            "<div><dt>" +
            escapeHtml(fieldLabel(code)) +
            "</dt><dd>" +
            escapeHtml(value) +
            "</dd></div>"
          );
        })
        .join("") +
      "</dl>";
  }

  function renderActions(availableActions) {
    hideCommentPanel();
    const list = availableActions || [];
    if (list.length === 0) {
      detailActions.innerHTML =
        '<p class="detail-empty">Нет доступных действий для вашей роли и текущего статуса.</p>';
      return;
    }
    detailActions.innerHTML = list
      .map(function (action) {
        const label = action.name || action.code || "—";
        return (
          '<button type="button" class="chip action-chip"' +
          ' data-id="' +
          escapeHtml(action.id) +
          '"' +
          ' data-code="' +
          escapeHtml(action.code || "") +
          '">' +
          escapeHtml(label) +
          "</button>"
        );
      })
      .join("");

    Array.prototype.forEach.call(detailActions.querySelectorAll(".action-chip"), function (btn) {
      btn.addEventListener("click", function () {
        if (actionBusy) return;
        clearActionError();
        const action = {
          id: btn.getAttribute("data-id"),
          code: btn.getAttribute("data-code") || "",
        };
        if (!action.id) return;
        if (COMMENT_REQUIRED[action.code]) {
          showCommentPanel(action);
          return;
        }
        executeAction(action.id, action.code, null);
      });
    });
  }

  function renderHistory(items) {
    if (!items || items.length === 0) {
      detailHistory.innerHTML = '<p class="detail-empty">Событий истории пока нет.</p>';
      return;
    }
    detailHistory.innerHTML =
      '<ul class="history-list">' +
      items
        .map(function (event) {
          const fromState = event.from_state || "—";
          const toState = event.to_state || "—";
          const comment = event.comment
            ? '<div class="history-comment">' + escapeHtml(event.comment) + "</div>"
            : "";
          const actor =
            event.actor_id != null
              ? '<span class="history-actor">' + escapeHtml(event.actor_id) + "</span>"
              : "";
          return (
            "<li>" +
            '<div class="history-row">' +
            '<span class="history-action">' +
            escapeHtml(event.action || "—") +
            "</span>" +
            '<span class="history-states">' +
            escapeHtml(fromState) +
            " → " +
            escapeHtml(toState) +
            "</span>" +
            '<span class="history-at">' +
            escapeHtml(formatDateTime(event.at)) +
            "</span>" +
            "</div>" +
            actor +
            comment +
            "</li>"
          );
        })
        .join("") +
      "</ul>";
  }

  function applyDetailPayload(card, history, actions) {
    renderMeta(card);
    renderValues(card.values);
    renderActions(actions && actions.available_actions);
    renderHistory(history && history.items);
    updateEditControls(card);
  }

  async function loadFieldNames(card) {
    fieldNameByCode = {};
    const typeId =
      card && card.request_type && card.request_type.id != null
        ? card.request_type.id
        : null;
    if (typeId == null) return;
    try {
      const schema = await apiFetch(
        "/request-types/" + encodeURIComponent(typeId) + "/schema"
      );
      const fields = (schema && schema.fields) || [];
      fields.forEach(function (field) {
        if (field && field.code) {
          fieldNameByCode[field.code] = field.name || field.code;
        }
      });
    } catch (_err) {
      // Optional labels: keep field_code fallback.
    }
  }

  async function fetchDetailParts() {
    return Promise.all([
      apiFetch("/requests/" + encodeURIComponent(requestId)),
      apiFetch("/requests/" + encodeURIComponent(requestId) + "/history"),
      apiFetch("/requests/" + encodeURIComponent(requestId) + "/available-actions"),
    ]);
  }

  async function loadDetail(options) {
    const opts = options || {};
    const soft = opts.soft === true;

    if (!requestId) {
      showPageError("Некорректный идентификатор заявки");
      return;
    }

    if (!soft) {
      stateLoading.hidden = false;
      stateError.hidden = true;
      detailContent.hidden = true;
      editValuesBtn.hidden = true;
      deferredEditBanner.hidden = true;
    }

    try {
      const results = await fetchDetailParts();
      const card = results[0];
      if (!soft) {
        await loadFieldNames(card);
      }
      applyDetailPayload(card, results[1], results[2]);
      clearActionError();
      stateLoading.hidden = true;
      stateError.hidden = true;
      detailContent.hidden = false;
    } catch (err) {
      const message =
        err && err.message
          ? err.message
          : "Произошла внутренняя ошибка. Попробуйте позже";
      if (soft && !detailContent.hidden) {
        showActionError(message);
      } else {
        showPageError(message);
      }
    }
  }

  async function executeAction(actionId, actionCode, comment) {
    if (!requestId || actionBusy) return;
    actionBusy = true;
    setActionsDisabled(true);
    clearActionError();

    const body = COMMENT_REQUIRED[actionCode] ? { comment: comment } : {};

    try {
      await apiFetch(
        "/requests/" +
          encodeURIComponent(requestId) +
          "/actions/" +
          encodeURIComponent(actionId),
        {
          method: "POST",
          body: body,
        }
      );
      hideCommentPanel();
      await loadDetail({ soft: true });
    } catch (err) {
      showActionError(
        err && err.message
          ? err.message
          : "Произошла внутренняя ошибка. Попробуйте позже"
      );
    } finally {
      actionBusy = false;
      setActionsDisabled(false);
    }
  }

  loadDetail();
})();
