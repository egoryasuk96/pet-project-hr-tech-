(function () {
  if (!Session.getAccessToken()) {
    window.location.replace("/login");
    return;
  }

  const userNameEl = document.getElementById("user-name");
  const logoutBtn = document.getElementById("logout-btn");
  const pageTitle = document.getElementById("page-title");
  const backLink = document.getElementById("back-link");
  const selectStep = document.getElementById("select-step");
  const formStep = document.getElementById("form-step");
  const catalogEl = document.getElementById("type-catalog");
  const stateLoading = document.getElementById("state-loading");
  const stateEmpty = document.getElementById("state-empty");
  const stateError = document.getElementById("state-error");
  const stateErrorMessage = document.getElementById("state-error-message");
  const retryBtn = document.getElementById("retry-btn");
  const formLoading = document.getElementById("form-loading");
  const formError = document.getElementById("form-error");
  const formErrorMessage = document.getElementById("form-error-message");
  const formContent = document.getElementById("form-content");
  const schemaFields = document.getElementById("schema-fields");
  const createForm = document.getElementById("create-form");
  const createSubmit = document.getElementById("create-submit");
  const createError = document.getElementById("create-error");
  const backToTypesBtn = document.getElementById("back-to-types-btn");
  const cancelFormBtn = document.getElementById("cancel-form-btn");

  const user = Session.getUser();
  userNameEl.textContent = (user && user.full_name) || "";

  let selectedTypeId = null;
  let submitting = false;

  logoutBtn.addEventListener("click", function () {
    Session.clear();
    window.location.href = "/login";
  });

  retryBtn.addEventListener("click", function () {
    loadTypes();
  });

  backToTypesBtn.addEventListener("click", function () {
    showSelectStep();
  });

  cancelFormBtn.addEventListener("click", function () {
    showSelectStep();
  });

  createForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    if (!selectedTypeId || submitting) return;
    clearCreateError();
    setSubmitting(true);

    try {
      const created = await apiFetch("/requests", {
        method: "POST",
        body: { request_type_id: Number(selectedTypeId) },
      });
      if (!created || created.id == null) {
        throw new Error("Сервер не вернул идентификатор заявки");
      }
      window.location.href = "/requests/" + encodeURIComponent(created.id);
    } catch (err) {
      showCreateError(
        err && err.message
          ? err.message
          : "Произошла внутренняя ошибка. Попробуйте позже"
      );
      setSubmitting(false);
    }
  });

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function hideSelectStates() {
    stateLoading.hidden = true;
    stateEmpty.hidden = true;
    stateError.hidden = true;
    catalogEl.hidden = true;
  }

  function showSelectStep() {
    selectedTypeId = null;
    submitting = false;
    pageTitle.textContent = "Выберите тип заявки";
    backLink.textContent = "← К списку";
    backLink.href = "/requests";
    backLink.onclick = null;
    selectStep.hidden = false;
    formStep.hidden = true;
    formLoading.hidden = true;
    formError.hidden = true;
    formContent.hidden = true;
    clearCreateError();
    if (catalogEl.innerHTML) {
      hideSelectStates();
      catalogEl.hidden = false;
    } else {
      loadTypes();
    }
  }

  function setSubmitting(isSubmitting) {
    submitting = isSubmitting;
    createSubmit.disabled = isSubmitting;
    createSubmit.textContent = isSubmitting ? "Создание…" : "Создать заявку";
  }

  function showCreateError(message) {
    createError.hidden = false;
    createError.textContent = message;
  }

  function clearCreateError() {
    createError.hidden = true;
    createError.textContent = "";
  }

  function renderTypes(items) {
    catalogEl.innerHTML = items
      .map(function (item) {
        const name = item.name || item.code || "Тип заявки";
        const description = item.description || "Без описания";
        return (
          '<button type="button" class="type-card" data-id="' +
          escapeHtml(item.id) +
          '" data-name="' +
          escapeHtml(name) +
          '">' +
          '<span class="type-card-name">' +
          escapeHtml(name) +
          "</span>" +
          '<span class="type-card-desc">' +
          escapeHtml(description) +
          "</span>" +
          "</button>"
        );
      })
      .join("");

    Array.prototype.forEach.call(catalogEl.querySelectorAll(".type-card"), function (btn) {
      btn.addEventListener("click", function () {
        const id = btn.getAttribute("data-id");
        const name = btn.getAttribute("data-name") || "Новая заявка";
        if (id) {
          openFormForType(id, name);
        }
      });
    });
  }

  async function loadTypes() {
    hideSelectStates();
    stateLoading.hidden = false;

    try {
      const items = await apiFetch("/request-types");
      hideSelectStates();
      if (!items || items.length === 0) {
        stateEmpty.hidden = false;
      } else {
        renderTypes(items);
        catalogEl.hidden = false;
      }
    } catch (err) {
      hideSelectStates();
      stateErrorMessage.textContent =
        err && err.message
          ? err.message
          : "Произошла внутренняя ошибка. Попробуйте позже";
      stateError.hidden = false;
    }
  }

  async function openFormForType(typeId, typeName) {
    selectedTypeId = typeId;
    pageTitle.textContent = typeName || "Новая заявка";
    backLink.textContent = "← К выбору типа";
    backLink.href = "#";
    backLink.onclick = function (event) {
      event.preventDefault();
      showSelectStep();
    };

    selectStep.hidden = true;
    formStep.hidden = false;
    formLoading.hidden = false;
    formError.hidden = true;
    formContent.hidden = true;
    clearCreateError();
    setSubmitting(false);

    try {
      const schema = await apiFetch(
        "/request-types/" + encodeURIComponent(typeId) + "/schema"
      );
      const fields = (schema && schema.fields) || [];
      SchemaForm.renderFields(schemaFields, fields);
      formLoading.hidden = true;
      formContent.hidden = false;
    } catch (err) {
      formLoading.hidden = true;
      formErrorMessage.textContent =
        err && err.message
          ? err.message
          : "Произошла внутренняя ошибка. Попробуйте позже";
      formError.hidden = false;
    }
  }

  loadTypes();
})();
