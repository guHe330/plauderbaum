// An open conversation: what happens when the learner starts one, answers,
// rewinds, switches branches or asks for another reply.
import { api } from "./api.js";
import { createChatView } from "./chat-view.js";
import { $, toast } from "./dom.js";
import { sessionOpen, showPage } from "./navigation.js";
import { autoSay, say, setConversationVoice } from "./speech.js";
import { state } from "./state.js";
import { loadConversation, saveConversation } from "./store.js";
import { ConversationTree } from "./tree.js";

const input = $("#input");
const sendButton = $("#composer button");
const view = createChatView($("#chat"), $("#tab-tutor"), {
  onRewind: rewindTo,
  onOtherReply: otherReply,
  onShowBranch: showBranch,
});

// While busy, nothing else can be started; the page dims what cannot be clicked.
function setBusy(busy) {
  state.busy = busy;
  document.body.classList.toggle("busy", busy);
  const closed = busy || !state.tree || state.tree.done;
  input.disabled = closed;
  sendButton.disabled = closed;
  view.setThinking(busy && sessionOpen());
  if (!closed && sessionOpen()) input.focus();
}

function languageName(tree) {
  return state.languages[tree.targetLanguage] || tree.targetLanguage;
}

// The voice for a conversation in another language than the one set in
// Settings: the one it was started with, or else the first for its language.
// For a conversation in the Settings language: null, the voice chosen there.
async function voiceFor(tree) {
  if (tree.targetLanguage === state.settings.target_language) return null;
  if (tree.voice) return tree.voice;
  try {
    const voices = await api(`/api/voices?lang=${encodeURIComponent(tree.targetLanguage)}`);
    return voices.length ? voices[0].id : null;
  } catch {
    return null;
  }
}

function show(tree, voice) {
  state.tree = tree;
  setConversationVoice(voice);
  $("#session-title").textContent = tree.title;
  $("#situation").textContent = tree.situation;
  input.placeholder = `Answer in ${languageName(tree)}, or in your native language when you are stuck`;
  showPage("session");
  view.renderPath(tree);
}

// What every model call for this conversation carries: the scenario, the lines
// down to `node`, and the language and level the conversation was started in.
function modelRequest(tree, node) {
  return {
    scenario: tree.scenario,
    situation: tree.situation,
    path: tree.pathTo(node).map(({ role, text }) => ({ role, text })),
    target_language: tree.targetLanguage,
    level: tree.level,
  };
}

export async function startConversation(scenario) {
  if (state.busy) return;
  setBusy(true);
  toast("Setting the scene…");
  try {
    const opening = await api("/api/start", { scenario });
    const tree = ConversationTree.start({
      id: crypto.randomUUID(),
      scenario,
      situation: opening.situation,
      targetLanguage: state.settings.target_language,
      level: state.settings.level,
      voice: state.settings.voice,
      created: new Date().toISOString(),
      text: opening.tutor_line,
      translation: opening.translation,
    });
    saveConversation(tree);
    show(tree, null);
    autoSay(tree.active.text);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

// Open a saved conversation. Returns false if it could not be loaded.
export async function openConversation(id) {
  if (state.busy) return true;
  setBusy(true);
  try {
    const tree = await loadConversation(id);
    show(tree, await voiceFor(tree));
    return true;
  } catch (error) {
    toast(error.message, true);
    return false;
  } finally {
    setBusy(false);
  }
}

async function sendMessage(text) {
  const tree = state.tree;
  const current = tree.active;
  const attempt = view.addAttempt(text);
  setBusy(true);
  try {
    const result = await api("/api/turn", { ...modelRequest(tree, current), text });
    view.setThinking(false);
    if (result.verdict === "ok") {
      const learner = tree.addLearnerLine(current, {
        text: result.ideal || text,
        typed: text,
        note: result.explanation,
      });
      const tutor = tree.addTutorLine(learner, {
        text: result.tutor_reply,
        translation: result.tutor_reply_translation,
        done: result.conversation_done,
      });
      tree.activate(tutor);
      saveConversation(tree);
      attempt.remove();
      view.appendLines(tree, [learner, tutor]);
      autoSay(tutor.text);
    } else {
      // the tree stays where it was, the learner tries this turn again
      view.addCorrection(attempt, result, languageName(tree));
      autoSay(result.ideal);
    }
  } catch (error) {
    attempt.remove();
    input.value = text;
    toast(error.message, true);
  } finally {
    setBusy(false);
    view.renderTail(tree);
    view.scrollDown();
  }
}

// Ask for another way the other person could have reacted; it becomes a new branch.
async function otherReply(node) {
  if (state.busy) return;
  const tree = state.tree;
  const learner = tree.node(node.parent);  // none for an opening line
  say();
  setBusy(true);
  try {
    const result = await api("/api/reply", {
      ...modelRequest(tree, learner),
      existing: tree.siblingsOf(node).map((sibling) => sibling.text),
    });
    const tutor = tree.addTutorLine(learner, {
      text: result.tutor_reply,
      translation: result.tutor_reply_translation,
      done: result.conversation_done,
    });
    tree.activate(tutor);
    saveConversation(tree);
    view.renderPath(tree);
    autoSay(tutor.text);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

// End the shown conversation on this tutor line, to answer it differently.
function rewindTo(node) {
  if (state.busy) return;
  say();
  state.tree.activate(node);
  saveConversation(state.tree);
  view.renderPath(state.tree);
  setBusy(false);
}

function showBranch(node) {
  if (state.busy) return;
  say();
  state.tree.showBranch(node);
  saveConversation(state.tree);
  view.renderPath(state.tree);
  setBusy(false);
}

$("#composer").addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || state.busy || !state.tree || state.tree.done) return;
  input.value = "";
  sendMessage(text);
});
