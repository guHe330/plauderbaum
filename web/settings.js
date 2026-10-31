// The Settings tab.
import { api } from "./api.js";
import { $, toast } from "./dom.js";
import { onLeavingSettings, showTab } from "./navigation.js";
import { sayIn } from "./speech.js";
import { state, targetName } from "./state.js";

const form = $("#settings-form");

// Input events only come from the user, not from the lists that load by themselves.
let unsaved = false;
form.addEventListener("input", () => { unsaved = true; });

const SELECTS = ["provider", "model", "target_language", "level", "strictness", "speech_rate"];

const TEST_PHRASES = {
  it: "Buongiorno! Che cosa desidera?",
  es: "¡Buenos días! ¿Qué desea?",
  fr: "Bonjour ! Qu'est-ce que vous désirez ?",
  pt: "Bom dia! O que deseja?",
  en: "Good morning! What would you like?",
  de: "Guten Morgen! Was darf es sein?",
};

// Take over settings from the server and update every text that depends on them.
function applySettings(settings) {
  state.settings = settings;
  $("#no-key").hidden = settings.has_key;
  const saved = "A key is saved. Leave this empty to keep it.";
  $("#key-status").textContent = settings.has_anthropic_key
    ? saved
    : "Create one at console.anthropic.com. It is kept in your system's credential store.";
  $("#openrouter-key-status").textContent = settings.has_openrouter_key
    ? saved
    : "Create one at openrouter.ai/keys. It is kept in your system's credential store.";
  $("#local-token-status").textContent = settings.has_local_token
    ? "A token is saved. Leave this empty to keep it."
    : "Only if your server requires one, like LM Studio with authentication on. It is kept in your system's credential store.";
  $("#remove-local-token").hidden = !settings.has_local_token;
  const name = targetName();
  document.querySelectorAll(".lang-name").forEach((node) => { node.textContent = name; });
}

async function loadVoices(language, selected) {
  const select = form.elements.voice;
  select.replaceChildren();
  try {
    const voices = await api(`/api/voices?lang=${encodeURIComponent(language)}`);
    for (const voice of voices) select.append(new Option(voice.label, voice.id));
    if (voices.some((voice) => voice.id === selected)) select.value = selected;
  } catch (error) {
    if (selected) select.append(new Option(selected, selected));
    toast(error.message, true);
  }
}

let openrouterModelsLoaded = false;
async function loadOpenrouterModels() {
  if (openrouterModelsLoaded) return;
  openrouterModelsLoaded = true;
  try {
    const models = await api("/api/openrouter-models");
    for (const model of models) $("#openrouter-models").append(new Option(model.label, model.id));
  } catch {
    // only suggestions: the model id can still be typed by hand
    openrouterModelsLoaded = false;
  }
}

// The local server's model list, keeping `selected` while it loads.
async function loadLocalModels(selected) {
  const select = form.elements.local_model;
  const status = $("#local-models-status");
  select.replaceChildren();
  if (selected) select.append(new Option(selected, selected));
  try {
    const models = await api(`/api/local-models?server=${encodeURIComponent(form.elements.local_server.value)}`);
    select.replaceChildren();
    for (const model of models) select.append(new Option(model.label, model.id));
    if (models.some((model) => model.id === selected)) select.value = selected;
    status.textContent = models.length
      ? "The models the server offers. Small models give much weaker corrections than Claude."
      : "The server has no models. Pull one in Ollama or load one in LM Studio.";
  } catch (error) {
    status.textContent = error.message;
  }
}

function showProvider(provider) {
  document.querySelectorAll("[data-provider]").forEach((block) => { block.hidden = block.dataset.provider !== provider; });
  if (provider === "openrouter") loadOpenrouterModels();
  if (provider === "local") loadLocalModels(state.settings.local_model);
}

function fillForm(settings) {
  for (const name of SELECTS) form.elements[name].value = settings[name];
  form.elements.openrouter_model.value = settings.openrouter_model;
  form.elements.local_server.value = settings.local_server;
  form.elements.auto_speak.checked = settings.auto_speak;
  showProvider(settings.provider);
}

function readForm() {
  const values = {
    auto_speak: form.elements.auto_speak.checked,
    api_key: form.elements.api_key.value,
    openrouter_api_key: form.elements.openrouter_api_key.value,
    openrouter_model: form.elements.openrouter_model.value,
    local_server: form.elements.local_server.value,
  };
  for (const name of [...SELECTS, "voice", "local_model"]) {
    if (form.elements[name].value) values[name] = form.elements[name].value;
  }
  const token = form.elements.local_token.value.trim();
  if (token) values.local_token = token;
  return values;
}

function clearSecrets() {
  form.elements.api_key.value = "";
  form.elements.openrouter_api_key.value = "";
  form.elements.local_token.value = "";
  $("#save-local-token").hidden = true;
}

function discardChanges() {
  unsaved = false;
  clearSecrets();
  fillForm(state.settings);
  loadVoices(state.settings.target_language, state.settings.voice);
}

async function saveSettings() {
  const values = readForm();
  const data = await api("/api/settings", values);
  applySettings(data.settings);
  clearSecrets();
  unsaved = false;
  // A new token can open up a model list that was refused.
  if (values.local_token) loadLocalModels(form.elements.local_model.value);
}

// Set the tab up with the answer of /api/settings. The returned promise
// resolves when the voice list has arrived, which takes a moment.
export function initSettings({ settings, languages, models }) {
  state.languages = languages;
  for (const [id, label] of Object.entries(models)) form.elements.model.append(new Option(label, id));
  for (const [id, label] of Object.entries(languages)) form.elements.target_language.append(new Option(label, id));
  applySettings(settings);
  fillForm(settings);
  return loadVoices(settings.target_language, settings.voice);
}

onLeavingSettings(() => {
  if (!unsaved) return;
  if (!confirm("Save your changes to Settings? Cancel discards them.")) {
    discardChanges();
    return;
  }
  saveSettings().then(() => toast("Saved"), (error) => {
    toast(error.message, true);
    showTab("settings");
  });
});

form.elements.provider.addEventListener("change", (event) => showProvider(event.target.value));
form.elements.local_server.addEventListener("change", () => loadLocalModels(form.elements.local_model.value));
form.elements.target_language.addEventListener("change", (event) => loadVoices(event.target.value));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await saveSettings();
    toast("Saved");
  } catch (error) {
    toast(error.message, true);
  }
});

form.elements.local_token.addEventListener("input", (event) => {
  $("#save-local-token").hidden = !event.target.value.trim();
});

$("#save-local-token").addEventListener("click", async () => {
  try {
    await saveSettings();
    toast("Token saved");
  } catch (error) {
    toast(error.message, true);
  }
});

$("#remove-local-token").addEventListener("click", async () => {
  try {
    const data = await api("/api/settings", { local_token: "" });
    applySettings(data.settings);
    loadLocalModels(form.elements.local_model.value);
    toast("Token removed");
  } catch (error) {
    toast(error.message, true);
  }
});

$("#test-voice").addEventListener("click", async () => {
  try {
    await saveSettings();
    sayIn(state.settings.voice, TEST_PHRASES[state.settings.target_language]);
  } catch (error) {
    toast(error.message, true);
  }
});
