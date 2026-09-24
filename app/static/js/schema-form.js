/* Schema-driven form helpers for Create Request (POST only; values deferred). */
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

  function renderField(field) {
    const code = field.code || "field";
    const name = field.name || code;
    const requiredMark = field.required
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
        '" disabled />' +
        "<span>" +
        escapeHtml(name) +
        "</span>" +
        "</label>";
      return (
        '<div class="field schema-field" data-code="' +
        escapeHtml(code) +
        '" data-type="' +
        escapeHtml(dataType) +
        '">' +
        control +
        "</div>"
      );
    }

    if (dataType === "catalog") {
      control =
        '<select id="' +
        escapeHtml(id) +
        '" name="' +
        escapeHtml(code) +
        '" disabled>' +
        renderCatalogOptions(field) +
        "</select>";
    } else if (dataType === "date") {
      control =
        '<input type="date" id="' +
        escapeHtml(id) +
        '" name="' +
        escapeHtml(code) +
        '" disabled />';
    } else if (dataType === "number") {
      control =
        '<input type="number" id="' +
        escapeHtml(id) +
        '" name="' +
        escapeHtml(code) +
        '" disabled />';
    } else {
      control =
        '<input type="text" id="' +
        escapeHtml(id) +
        '" name="' +
        escapeHtml(code) +
        '" disabled />';
    }

    return (
      '<div class="field schema-field" data-code="' +
      escapeHtml(code) +
      '" data-type="' +
      escapeHtml(dataType) +
      '">' +
      '<label for="' +
      escapeHtml(id) +
      '">' +
      escapeHtml(name) +
      requiredMark +
      "</label>" +
      control +
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

  return {
    renderFields: renderFields,
    sortFields: sortFields,
  };
})();
