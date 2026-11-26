"use strict";

const $ = (selector) => document.querySelector(selector);
const labels = {
  "print-models": { title: "Модели за печат", singular: "модел", add: "Добави модел" },
  designers: { title: "Дизайнери", singular: "дизайнер", add: "Добави дизайнер" },
  categories: { title: "Категории", singular: "категория", add: "Добави категория" },
  materials: { title: "Материали", singular: "материал", add: "Добави материал" },
};
const difficulties = { easy: "Лесно", medium: "Средно", hard: "Трудно" };
const state = { view: "print-models", data: {}, model: null, links: [], editor: null, materialId: null };
let catalogRequest = 0;
let detailsRequest = 0;

// All text from the API is inserted as text, never interpreted as HTML.
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function message(selector, text = "") {
  const node = $(selector);
  node.textContent = text;
  node.hidden = !text;
}

function action(text, handler, className = "") {
  const button = element("button", className, text);
  button.type = "button";
  button.addEventListener("click", () => runAction(handler));
  return button;
}

async function runAction(handler) {
  const target = $("#details-dialog").open ? "#material-error" : $("#designer-dialog").open ? "#designer-error" : "#page-error";
  message(target);
  try { await handler(); } catch (error) { message(target, error.message); }
}

function validationMessage(detail) {
  if (!Array.isArray(detail)) return typeof detail === "string" ? detail : "Заявката не може да бъде изпълнена.";
  const fieldNames = { name: "Име", email: "Имейл", instructions: "Инструкции", difficulty: "Трудност", copies: "Брой копия", print_time_minutes: "Време за печат", designer_id: "Дизайнер", category_id: "Категория", material_id: "Материал", quantity: "Количество", unit: "Единица" };
  return detail.map((item) => `${fieldNames[item.loc?.at(-1)] || "Стойност"}: ${item.msg}`).join("; ");
}

async function api(path, method = "GET", data) {
  let response;
  try {
    response = await fetch(path, {
      method,
      cache: "no-store",
      headers: data === undefined ? {} : { "Content-Type": "application/json" },
      body: data === undefined ? undefined : JSON.stringify(data),
    });
  } catch {
    throw new Error("Няма връзка със сървъра. Провери дали приложението е стартирано и опитай отново.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(`${validationMessage(body.message ?? body.detail)} (HTTP ${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

function fillOptions(select, entries, placeholder, selected = "") {
  select.replaceChildren();
  if (placeholder !== null) select.add(new Option(placeholder, ""));
  for (const entry of entries) select.add(new Option(entry.name, String(entry.id)));
  select.value = String(selected ?? "");
}

async function loadReferenceData() {
  const resources = ["designers", "categories", "materials"];
  const results = await Promise.all(resources.map((resource) => api(`/${resource}`)));
  resources.forEach((resource, index) => {
    state.data[resource] = results[index];
    $(`#count-${resource}`).textContent = results[index].length;
  });
  const previous = $("#filter-category").value;
  fillOptions($("#filter-category"), state.data.categories, "Всички категории", previous);
}

function relatedName(resource, id, fallback = "Без категория") {
  return state.data[resource]?.find((entry) => entry.id === id)?.name ?? fallback;
}

function emptyState(title, description) {
  const box = element("div", "empty-state");
  box.append(element("h3", "", title), element("p", "", description));
  return box;
}

function modelCard(model, manage = true) {
  const card = element("article", "model-card");
  const heading = element("div", "model-heading");
  heading.append(element("span", "model-number", `#${String(model.id).padStart(3, "0")}`), element("h3", "", model.name), element("p", "byline", relatedName("designers", model.designer_id, "Неизвестен дизайнер")));
  const time = element("div", "model-time");
  time.append(element("strong", "", `${model.print_time_minutes} мин.`), element("span", "", `${model.copies} копия`));
  const actions = element("div", "card-actions");
  actions.append(action("Детайли", () => openDetails(model.id)));
  if (manage) actions.append(
    action("Редакция", () => openEditor("print-models", model.id)),
    action("Изтрий", () => deleteResource("print-models", model), "danger"),
  );
  card.append(heading, element("p", "model-category", relatedName("categories", model.category_id)), element("span", `difficulty ${model.difficulty}`, difficulties[model.difficulty]), time, actions);
  return card;
}

function renderModels(container, models, filtered = false, manage = true) {
  container.replaceChildren();
  if (!models.length) {
    container.append(emptyState(filtered ? "Няма съвпадения" : "Все още няма модели", filtered ? "Промени филтрите и потърси отново." : "Добави дизайнер, а след това създай първия модел."));
  } else {
    container.append(...models.map((model) => modelCard(model, manage)));
  }
}

async function loadCatalog() {
  const request = ++catalogRequest;
  const query = new URLSearchParams();
  for (const [key, value] of new FormData($("#filters"))) if (value.trim()) query.set(key, value.trim());
  $("#model-list").setAttribute("aria-busy", "true");
  try {
    const models = await api(`/print-models?${query}`);
    if (request !== catalogRequest) return;
    renderModels($("#model-list"), models, query.size > 0);
    $("#result-count").textContent = `${models.length} резултата`;
    // The navigation count describes all models, independent of active filters.
    const all = query.size ? await api("/print-models") : models;
    if (request === catalogRequest) $("#count-print-models").textContent = all.length;
  } finally {
    if (request === catalogRequest) $("#model-list").setAttribute("aria-busy", "false");
  }
}

function renderRegistry() {
  if (state.view === "print-models") return;
  const resource = state.view;
  const container = $("#registry-list");
  container.replaceChildren();
  const entries = state.data[resource] || [];
  if (!entries.length) {
    container.append(emptyState("Все още няма записи", `Използвай „${labels[resource].add}“, за да започнеш.`));
  }
  for (const entry of entries) {
    const row = element("article", "registry-row");
    const info = element("div");
    info.append(element("h3", "", entry.name), element("p", "muted", resource === "designers" ? entry.email : `ID: ${entry.id}`));
    const actions = element("div", "row-actions");
    if (resource === "designers") actions.append(action("Виж модели", () => openDesigner(entry)));
    actions.append(action("Редакция", () => openEditor(resource, entry.id)), action("Изтрий", () => deleteResource(resource, entry), "danger"));
    row.append(info, actions);
    container.append(row);
  }
}

function switchView(resource) {
  state.view = resource;
  message("#page-error");
  message("#notice");
  for (const button of document.querySelectorAll("[data-view]")) {
    const active = button.dataset.view === resource;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current");
  }
  $("#page-title").textContent = labels[resource].title;
  $("#create-button").textContent = labels[resource].add;
  $("#catalog-view").hidden = resource !== "print-models";
  $("#registry-view").hidden = resource === "print-models";
  renderRegistry();
}

async function refresh() {
  await loadReferenceData();
  await loadCatalog();
  renderRegistry();
}

function addField(name, title, type, value, full = false) {
  const label = element("label", full ? "full-width" : "", title);
  const input = element(type === "textarea" ? "textarea" : type === "select" ? "select" : "input");
  input.name = name;
  input.id = `edit-${name}`;
  if (input.tagName === "INPUT") input.type = type;
  input.required = name !== "category_id";
  if (type === "number") { input.min = "1"; input.step = "1"; input.max = String(Number.MAX_SAFE_INTEGER); }
  if (value !== undefined && type !== "select") input.value = value;
  label.append(input);
  $("#editor-fields").append(label);
  return input;
}

async function openEditor(resource, id = null) {
  const record = id === null ? {} : await api(`/${resource}/${id}`);
  if (resource === "print-models" && !state.data.designers?.length) {
    message("#page-error", "Първо добави дизайнер от раздел „Дизайнери“. След това можеш да създадеш модел.");
    return;
  }
  state.editor = { resource, id };
  $("#editor-title").textContent = `${id === null ? "Добавяне на" : "Редакция на"} ${labels[resource].singular}`;
  $("#editor-fields").replaceChildren();
  message("#editor-error");
  addField("name", "Име", "text", record.name, true);
  if (resource === "designers") addField("email", "Имейл", "email", record.email, true);
  if (resource === "print-models") {
    fillOptions(addField("designer_id", "Дизайнер", "select"), state.data.designers, "Избери дизайнер", record.designer_id);
    fillOptions(addField("category_id", "Категория", "select"), state.data.categories, "Без категория", record.category_id);
    const difficulty = addField("difficulty", "Трудност", "select");
    difficulty.add(new Option("Избери трудност", ""));
    Object.entries(difficulties).forEach(([value, text]) => difficulty.add(new Option(text, value)));
    difficulty.value = record.difficulty || "";
    addField("copies", "Брой копия", "number", record.copies ?? 1);
    addField("print_time_minutes", "Време за печат (минути)", "number", record.print_time_minutes);
    addField("instructions", "Инструкции за печат", "textarea", record.instructions, true);
  }
  $("#editor-dialog").showModal();
}

async function submitForm(form, errorSelector, handler) {
  if (form.dataset.busy) return;
  form.dataset.busy = "true";
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  message(errorSelector);
  try { await handler(); } catch (error) { message(errorSelector, error.message); }
  finally { delete form.dataset.busy; button.disabled = false; }
}

async function saveEditor() {
  const { resource, id } = state.editor;
  const data = Object.fromEntries(new FormData($("#editor-form")));
  if (resource === "print-models") {
    for (const key of ["copies", "print_time_minutes", "designer_id"]) data[key] = Number(data[key]);
    data.category_id = data.category_id ? Number(data.category_id) : null;
  }
  await api(`/${resource}${id === null ? "" : `/${id}`}`, id === null ? "POST" : "PUT", data);
  $("#editor-dialog").close();
  // Refresh failures are separate from saving: the successful write must not be repeated.
  await runAction(refresh);
  message("#notice", "Записът е запазен успешно.");
}

async function deleteResource(resource, record) {
  let warning = "";
  if (resource === "categories") warning = " Моделите ще се запазят без категория.";
  if (resource === "print-models") warning = " Връзките към материалите ще бъдат премахнати; самите материали се запазват.";
  if (!window.confirm(`Да се изтрие ли „${record.name}“?${warning}`)) return;
  await api(`/${resource}/${record.id}`, "DELETE");
  await refresh();
  message("#notice", "Записът е изтрит успешно.");
}

async function openDesigner(designer) {
  const models = await api(`/designers/${designer.id}/print-models`);
  $("#designer-title").textContent = `Модели на ${designer.name}`;
  message("#designer-error");
  renderModels($("#designer-models"), models, false, false);
  $("#designer-dialog").showModal();
}

function resetMaterialForm() {
  state.materialId = null;
  $("#material-form").reset();
  const available = state.data.materials.filter((material) => !state.links.some((link) => link.material_id === material.id));
  fillOptions($("#link-material"), available, available.length ? "Избери материал" : "Няма свободни материали");
  $("#link-material").disabled = false;
  $("#save-material").textContent = "Добави";
  $("#cancel-material").hidden = true;
  message("#material-error");
}

function editMaterial(link) {
  if ($("#material-form").dataset.busy) return;
  state.materialId = link.material_id;
  fillOptions($("#link-material"), [link.material], null, link.material_id);
  $("#link-material").disabled = true;
  $("#material-form").elements.quantity.value = link.quantity;
  $("#material-form").elements.unit.value = link.unit;
  $("#save-material").textContent = "Запази";
  $("#cancel-material").hidden = false;
  message("#material-error");
  $("#material-form").elements.quantity.focus();
}

async function removeMaterial(link) {
  if ($("#material-form").dataset.busy) return;
  if (!window.confirm(`Да се премахне ли „${link.material.name}“ от този модел? Материалът ще се запази в каталога.`)) return;
  await api(`/print-models/${state.model.id}/materials/${link.material_id}`, "DELETE");
  await reloadMaterials();
}

async function reloadMaterials() {
  const modelId = state.model.id;
  const links = await api(`/print-models/${modelId}/materials`);
  if (state.model.id !== modelId) return;
  state.links = links;
  renderMaterials();
}

function renderMaterials() {
  const container = $("#model-materials");
  container.replaceChildren();
  $("#material-count").textContent = String(state.links.length).padStart(2, "0");
  if (!state.links.length) container.append(element("p", "muted", "Към модела все още няма добавени материали."));
  for (const link of state.links) {
    const row = element("div", "material-row");
    const actions = element("div", "row-actions");
    // Errors inside the modal must remain visible there.
    const safe = (handler) => async () => {
      try { await handler(); } catch (error) { message("#material-error", error.message); }
    };
    actions.append(action("Редакция", safe(() => editMaterial(link))), action("Премахни", safe(() => removeMaterial(link)), "danger"));
    const label = element("span", "material-label");
    label.append(element("strong", "", link.material.name), document.createTextNode(" · "), element("span", "material-amount", `${formatQuantity(link.quantity)} ${link.unit}`));
    row.append(label, actions);
    container.append(row);
  }
  resetMaterialForm();
  $("#scale-result").replaceChildren();
  message("#scale-error");
}

function formatQuantity(value) {
  // Preserve very small positive quantities instead of displaying a misleading zero.
  return new Intl.NumberFormat("bg-BG", { maximumSignificantDigits: 10 }).format(value);
}

async function openDetails(id) {
  const request = ++detailsRequest;
  const [model, links] = await Promise.all([
    api(`/print-models/${id}`),
    api(`/print-models/${id}/materials`),
  ]);
  if (request !== detailsRequest) return;
  state.model = model;
  state.links = links;
  $("#details-id").textContent = `МОДЕЛ / #${String(model.id).padStart(3, "0")}`;
  $("#details-title").textContent = model.name;
  const body = $("#details-body");
  body.replaceChildren();
  const stats = element("dl", "detail-stats");
  for (const [title, value] of [
    ["Време за печат", `${model.print_time_minutes} мин.`],
    ["Копия", String(model.copies)],
    ["Трудност", difficulties[model.difficulty]],
  ]) {
    const group = element("div");
    group.append(element("dt", "", title), element("dd", "", value));
    stats.append(group);
  }
  const facts = element("dl", "detail-facts");
  const values = [
    ["Дизайнер", relatedName("designers", model.designer_id)],
    ["Категория", relatedName("categories", model.category_id)],
  ];
  for (const [title, value] of values) {
    const group = element("div");
    group.append(element("dt", "", title), element("dd", "", value));
    facts.append(group);
  }
  body.append(stats, facts, element("h3", "", "Инструкции за печат"), element("p", "instructions", model.instructions));
  $("#materials-hint").textContent = `Общо количество за записаните ${model.copies} копия.`;
  $("#scale-form").reset();
  renderMaterials();
  $("#details-dialog").showModal();
}

async function saveMaterial() {
  const form = $("#material-form");
  const quantity = Number(form.elements.quantity.value);
  if (!Number.isFinite(quantity) || quantity <= 0) throw new Error("Количеството трябва да е положително крайно число.");
  const editing = state.materialId !== null;
  const data = { quantity, unit: form.elements.unit.value };
  if (!editing) data.material_id = Number(form.elements.material_id.value);
  await api(`/print-models/${state.model.id}/materials${editing ? `/${state.materialId}` : ""}`, editing ? "PUT" : "POST", data);
  await reloadMaterials();
}

async function scaleModel() {
  $("#scale-result").replaceChildren();
  const copies = $("#scale-form").elements.copies.value;
  const model = await api(`/print-models/${state.model.id}/scaled?copies=${encodeURIComponent(copies)}`);
  const output = $("#scale-result");
  output.replaceChildren(element("strong", "", `За ${model.copies} копия:`));
  if (!model.materials.length) { output.append(element("p", "muted", "Няма добавени материали за преизчисляване.")); return; }
  const list = element("ul");
  model.materials.forEach((link) => {
    const item = element("li");
    item.append(element("span", "", `${link.material.name}: `), element("strong", "", `${formatQuantity(link.quantity)} ${link.unit}`));
    list.append(item);
  });
  output.append(list);
}

for (const button of document.querySelectorAll("[data-view]")) button.addEventListener("click", () => switchView(button.dataset.view));
for (const button of document.querySelectorAll("[data-close]")) button.addEventListener("click", () => {
  const dialog = document.getElementById(button.dataset.close);
  if (!dialog.querySelector('[data-busy="true"]')) dialog.close();
});
for (const dialog of document.querySelectorAll("dialog")) dialog.addEventListener("cancel", (event) => {
  if (dialog.querySelector('[data-busy="true"]')) event.preventDefault();
});
$("#create-button").addEventListener("click", () => runAction(() => openEditor(state.view)));
$("#filters").addEventListener("submit", (event) => { event.preventDefault(); runAction(loadCatalog); });
$("#reset-filters").addEventListener("click", () => { $("#filters").reset(); runAction(loadCatalog); });
$("#cancel-material").addEventListener("click", () => { if (!$("#material-form").dataset.busy) resetMaterialForm(); });
for (const [form, error, handler] of [
  ["#editor-form", "#editor-error", saveEditor],
  ["#material-form", "#material-error", saveMaterial],
  ["#scale-form", "#scale-error", scaleModel],
]) $(form).addEventListener("submit", (event) => { event.preventDefault(); submitForm($(form), error, handler); });

runAction(refresh);
