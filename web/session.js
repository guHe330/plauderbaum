// An open conversation: what happens when the learner starts one, answers,
// rewinds, switches branches or asks for another reply.
import { api } from "./api.js";
import { createChatView } from "./chat-view.js";
import { $, toast } from "./dom.js";
import { sessionOpen, showPage } from "./navigation.js";
import { autoSay, say } from "./speech.js";
import { state, targetName } from "./state.js";
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

function show(tree) {
  state.tree = tree;
  $("#session-title").textContent = tree.title;
  $("#situation").textContent = tree.situation;
  showPage("session");
  view.renderPath(tree);
}

// The lines down to `node` as the server wants them for a model call.
function linesTo(tree, node) {
  return tree.pathTo(node).map(({ role, text }) => ({ role, text }));
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
      created: new Date().toISOString(),
      text: opening.tutor_line,
      translation: opening.translation,
    });
    saveConversation(tree);
    show(tree);
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
    show(tree);
    if (tree.targetLanguage !== state.settings.target_language) {
      const name = state.languages[tree.targetLanguage] || tree.targetLanguage;
      toast(`This conversation is in ${name}. Switch "I am learning" in Settings to continue it.`, true);
    }
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
    const result = await api("/api/turn", {
      scenario: tree.scenario,
      situation: tree.situation,
      path: linesTo(tree, current),
      text,
    });
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
      view.addCorrection(attempt, result, targetName());
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
      scenario: tree.scenario,
      situation: tree.situation,
      path: linesTo(tree, learner),
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
