// Entry point: loads the settings, then the start page.
import { api } from "./api.js";
import { toast } from "./dom.js";
import { loadConversations, loadScenarios } from "./home.js";
import { showTab } from "./navigation.js";
import { initSettings } from "./settings.js";

async function init() {
  if (location.hash === "#settings") showTab("settings");
  try {
    const voicesLoaded = initSettings(await api("/api/settings"));
    await loadScenarios();
    await loadConversations();
    await voicesLoaded;
  } catch (error) {
    toast(error.message, true);
  }
}

init();
