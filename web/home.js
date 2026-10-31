// The start page: scenarios, a topic of your own, and earlier conversations.
import { api } from "./api.js";
import { $, ask, el, linkButton, toast } from "./dom.js";
import { showPage, showTab } from "./navigation.js";
import { openConversation, startConversation } from "./session.js";
import { say, setConversationVoice } from "./speech.js";
import { state } from "./state.js";
import { deleteConversation, listConversations } from "./store.js";

// Leave an open conversation (it is saved) and go back to the start page.
export async function showHome() {
  if (state.busy || !(await showTab("tutor"))) return;
  say();
  setConversationVoice(null);
  showPage("home");
  loadConversations();
}

export async function loadScenarios() {
  const scenarios = await api("/api/scenarios");
  const grid = $("#scenarios");
  for (const scenario of scenarios) {
    const button = el("button", "scenario");
    button.type = "button";
    button.append(el("span", "icon", scenario.icon), el("span", "", scenario.title));
    button.addEventListener("click", () => startConversation({ title: scenario.title, brief: scenario.brief }));
    grid.append(button);
  }
}

function savedRow(saved) {
  const row = el("div", "saved");
  const open = el("button", "open");
  open.type = "button";
  const when = saved.updated
    ? new Date(saved.updated).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })
    : "";
  const language = state.languages[saved.target_language] || saved.target_language;
  open.append(
    el("span", "title", saved.title),
    el("span", "meta", [language, `${saved.lines} lines`, when].filter(Boolean).join(" · ")),
  );
  open.addEventListener("click", async () => {
    if (!(await openConversation(saved.id))) loadConversations();
  });
  row.append(open, linkButton("Delete", () => removeConversation(saved)));
  return row;
}

async function removeConversation(saved) {
  if (state.busy) return;
  const answer = await ask(`Delete "${saved.title}" with all its branches?`, [
    { label: "Cancel", value: "cancel", className: "secondary" },
    { label: "Delete", value: "delete", className: "danger" },
  ]);
  if (answer !== "delete") return;
  try {
    await deleteConversation(saved.id);
  } catch (error) {
    toast(error.message, true);
  }
  loadConversations();
}

export async function loadConversations() {
  let conversations;
  try {
    conversations = await listConversations();
  } catch (error) {
    toast(error.message, true);
    return;
  }
  $("#history-list").replaceChildren(...conversations.map(savedRow));
  $("#history").hidden = conversations.length === 0;
}

$("#custom-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const topic = $("#custom-topic").value.trim();
  if (!topic) return;
  startConversation({
    title: topic,
    brief: "The learner chose this topic themselves. Pick a fitting everyday situation and a role for yourself.",
  });
});

$("#home").addEventListener("click", showHome);
$("#leave").addEventListener("click", showHome);
