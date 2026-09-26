/* Schema-driven form helpers for Create Request (values on POST). */
window.SchemaForm = (function () {
  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function sortFields(fields) {
    return (fields || []).slice().sort(function (a, b) {
      const ao = a.order_no != null ? a.order_no : 0;
      const bo = b.order_no != null ? b.order_no : 0;
      return ao - bo;
    });
  }

  function renderCatalogOptions(field) {
    const items =
      field.dictionary && field.dictionary.items ? field.dictionary.items : [];
    const options = ['<option value="">Выберите значение</option>'].concat(
      items.map(function (item) {
        return (
          '<option value="' +
          escapeHtml(item.id) +
          '">' +
          escapeHtml(item.name || item.code || item.id) +
          "</option>"
        );
      })
    );
    return options.join("");
  }

  function fieldErrorHtml() {
    return '<p class="field-error" hidden></p>';
  }

  function renderField(field) {
    const code = field.code || "field";
    const name = field.name || code;
    const required = !!field.required;
    const requiredMark = required
      ? ' <span class="field-required" aria-hidden="true">*</span>'
      : "";
    const id = "schema-field-" + code;
    const dataType = field.data_type || "text";
    let control = "";

    if (dataType === "boolean") {
      control =
        '<label class="field-checkbox">' +
        '<input type="checkbox" id="' +
        escapeHtml(id) +
        '" name="' +
        escapeHtml(code) +
        '" />' +
        "<span>" +
        escapeHtml(name) +
        "</span>" +
        "</label>";
      return (
        '<div class="field schema-field" data-code="' +
        escapeHtml(code) +
        '" data-type="' +
        escapeHtml(dataType) +
        '" data-required="' +
        (required ? "true" : "false") +
        '">' +
        control +
        fieldErrorHtml() +
        "</div>"
      );
    }

    if (dataType === "catalog") {
      control =
        '<select id="' +
        escapeHtml(id) +
        '" name="' +
        escapeHtml(code) +
        '">' +
        renderCatalogOptions(field) +
        "</select>";
    } else if (dataType === "date") {
      control =
        '<input type="date" id="' +
        escapeHtml(id) +
        '" name="' +
        escapeHtml(code) +
        '" />';
    } else if (dataType === "number") {
      control =
        '<input type="number" id="' +
        escapeHtml(id) +
        '" name="' +
        escapeHtml(code) +
        '" />';
    } else {
      control =
        '<input type="text" id="' +
        escapeHtml(id) +
        '" name="' +
        escapeHtml(code) +
        '" />';
    }

    return (
      '<div class="field schema-field" data-code="' +
      escapeHtml(code) +
      '" data-type="' +
      escapeHtml(dataType) +
      '" data-required="' +
      (required ? "true" : "false") +
      '">' +
      '<label for="' +
      escapeHtml(id) +
      '">' +
      escapeHtml(name) +
      requiredMark +
      "</label>" +
      control +
      fieldErrorHtml() +
      "</div>"
    );
  }

  function renderFields(container, fields) {
    if (!container) return;
    const sorted = sortFields(fields);
    if (sorted.length === 0) {
      container.innerHTML =
        '<p class="detail-empty">У выбранного типа нет полей схемы.</p>';
      return;
    }
    container.innerHTML = sorted.map(renderField).join("");
  }

  function readControlValue(fieldEl) {
    const type = fieldEl.getAttribute("data-type");
    const input = fieldEl.querySelector("input, select");
    if (!input) return null;
    if (type === "boolean") {
      return input.checked ? "true" : "";
    }
    return (input.value || "").trim();
  }

  function collectValues(container) {
    const out = [];
    if (!container) return out;
    container.querySelectorAll(".schema-field").forEach(function (el) {
      const code = el.getAttribute("data-code");
      if (!code) return;
      const value = readControlValue(el);
      if (value != null && value !== "") {
        out.push({ field_code: code, value: value });
      }
    });
    return out;
  }

  function clearFieldErrors(container) {
    if (!container) return;
    container.querySelectorAll(".field-error").forEach(function (p) {
      p.hidden = true;
      p.textContent = "";
    });
  }

  function validateRequired(container) {
    const missing = [];
    if (!container) return missing;
    clearFieldErrors(container);
    container
      .querySelectorAll('.schema-field[data-required="true"]')
      .forEach(function (el) {
        const value = readControlValue(el);
        if (value == null || value === "") {
          missing.push(el.getAttribute("data-code"));
          const err = el.querySelector(".field-error");
          if (err) {
            err.textContent = "Обязательное поле";
            err.hidden = false;
          }
        }
      });
    return missing;
  }

  return {
    renderFields: renderFields,
    sortFields: sortFields,
    collectValues: collectValues,
    validateRequired: validateRequired,
    clearFieldErrors: clearFieldErrors,
  };
})();
