// The Settings tab.
import { api } from "./api.js";
import { $, toast } from "./dom.js";
import { say } from "./speech.js";
import { state, targetName } from "./state.js";

const form = $("#settings-form");

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
  const name = targetName();
  document.querySelectorAll(".lang-name").forEach((node) => { node.textContent = name; });
  $("#input").placeholder = `Answer in ${name}, or in your native language when you are stuck`;
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

function showProvider(provider) {
  document.querySelectorAll("[data-provider]").forEach((block) => { block.hidden = block.dataset.provider !== provider; });
  if (provider === "openrouter") loadOpenrouterModels();
}

function fillForm(settings) {
  for (const name of SELECTS) form.elements[name].value = settings[name];
  form.elements.openrouter_model.value = settings.openrouter_model;
  form.elements.auto_speak.checked = settings.auto_speak;
  showProvider(settings.provider);
}

function readForm() {
  const values = {
    auto_speak: form.elements.auto_speak.checked,
    api_key: form.elements.api_key.value,
    openrouter_api_key: form.elements.openrouter_api_key.value,
    openrouter_model: form.elements.openrouter_model.value,
  };
  for (const name of [...SELECTS, "voice"]) {
    if (form.elements[name].value) values[name] = form.elements[name].value;
  }
  return values;
}

async function saveSettings() {
  const data = await api("/api/settings", readForm());
  applySettings(data.settings);
  form.elements.api_key.value = "";
  form.elements.openrouter_api_key.value = "";
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

form.elements.provider.addEventListener("change", (event) => showProvider(event.target.value));
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

$("#test-voice").addEventListener("click", async () => {
  try {
    await saveSettings();
    say(TEST_PHRASES[state.settings.target_language]);
  } catch (error) {
    toast(error.message, true);
  }
});
