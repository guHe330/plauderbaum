// Entry point: loads the settings, then the start page.
import { api } from "./api.js";
import { $, toast } from "./dom.js";
import { loadConversations, loadScenarios } from "./home.js";
import { showTab } from "./navigation.js";
import { initSettings } from "./settings.js";

async function init() {
  if (location.hash === "#settings") showTab("settings");
  try {
    const data = await api("/api/settings");
    $("#version").textContent = `Plauderbaum ${data.version}`;
    const voicesLoaded = initSettings(data);
    await loadScenarios();
    await loadConversations();
    await voicesLoaded;
  } catch (error) {
    toast(error.message, true);
  }
}

init();
