// Which part of the app is visible: the two tabs in the header, and inside the
// Tutor tab either the start page or an open conversation.
import { $ } from "./dom.js";

export function showTab(name) {
  for (const tab of document.querySelectorAll(".tabs button")) {
    tab.setAttribute("aria-selected", String(tab.dataset.tab === name));
  }
  $("#tab-tutor").hidden = name !== "tutor";
  $("#tab-settings").hidden = name !== "settings";
}

// `page` is "home" or "session".
export function showPage(page) {
  $("#picker").hidden = page !== "home";
  $("#session").hidden = page !== "session";
}

export function sessionOpen() {
  return !$("#session").hidden;
}

document.querySelectorAll(".tabs button").forEach((tab) =>
  tab.addEventListener("click", () => showTab(tab.dataset.tab)));
document.querySelectorAll("[data-goto]").forEach((link) =>
  link.addEventListener("click", (event) => { event.preventDefault(); showTab(link.dataset.goto); }));
