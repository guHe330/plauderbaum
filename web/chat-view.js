// Draws a conversation into the chat area. It only shows things: what a click
// on "Answer from here", "Other reply" or a branch does is up to the handlers
// {onRewind(node), onOtherReply(node), onShowBranch(node)}.
import { el, linkButton } from "./dom.js";
import { say, speakButton } from "./speech.js";

const CORRECTION_LABELS = {
  has_errors: () => "Almost. Say it like this",
  other_language: (language) => `In ${language}`,
  question: () => "Answer",
  unclear: () => "I did not understand that",
};

export function createChatView(chat, scroller, handlers) {
  function scrollDown() {
    scroller.scrollTop = scroller.scrollHeight;
  }

  // ‹ 2/3 › to move between the versions of one turn; nothing if there is only one.
  function switcher(tree, node) {
    const siblings = tree.siblingsOf(node);
    if (siblings.length < 2) return null;
    const index = siblings.indexOf(node);
    const box = el("span", "switcher");
    const previous = linkButton("‹", () => handlers.onShowBranch(siblings[index - 1]));
    const next = linkButton("›", () => handlers.onShowBranch(siblings[index + 1]));
    previous.title = "Previous version";
    next.title = "Next version";
    previous.disabled = index === 0;
    next.disabled = index === siblings.length - 1;
    box.append(previous, el("span", "", `${index + 1}/${siblings.length}`), next);
    return box;
  }

  function tutorLine(tree, node) {
    const bubble = el("div", "msg tutor");
    bubble.dataset.id = node.id;
    bubble.append(el("p", "text", node.text));
    const tools = el("div", "tools");
    tools.append(speakButton(node.text));
    if (node.translation) {
      const shown = el("p", "translation", node.translation);
      shown.hidden = true;
      tools.append(linkButton("Translation", () => { shown.hidden = !shown.hidden; }));
      bubble.append(shown);
    }
    tools.append(
      linkButton("↩ Answer from here", () => handlers.onRewind(node), "rewind"),
      linkButton("⟳ Other reply", () => handlers.onOtherReply(node)),
    );
    const versions = switcher(tree, node);
    if (versions) tools.append(versions);
    bubble.append(tools);
    return [bubble];
  }

  function learnerLine(tree, node) {
    const typed = node.typed || node.text;
    const bubble = el("div", "msg learner");
    bubble.append(el("p", "", typed));
    const versions = switcher(tree, node);
    if (versions) {
      const tools = el("div", "tools");
      tools.append(versions);
      bubble.append(tools);
    }
    const parts = [bubble];
    if (node.text !== typed || node.note) {
      const note = el("div", "note");
      if (node.text !== typed) note.append(el("b", "", `✓ ${node.text}`), document.createElement("br"));
      if (node.note) note.append(node.note);
      parts.push(note);
    }
    return parts;
  }

  function line(tree, node) {
    return node.role === "tutor" ? tutorLine(tree, node) : learnerLine(tree, node);
  }

  function summaryCard(tree) {
    const card = el("div", "card summary");
    card.append(el("div", "label", "Your ideal conversation"));
    const lines = tree.activePath;
    for (const node of lines) {
      const row = el("div", "turn");
      row.append(el("span", "who", node.role === "tutor" ? "Tutor" : "You"), el("span", "", node.text));
      card.append(row);
    }
    const actions = el("div", "actions");
    const playAll = el("button", "secondary", "🔊 Play it all");
    playAll.type = "button";
    playAll.addEventListener("click", () => say(...lines.map((node) => node.text)));
    actions.append(playAll);
    card.append(actions);
    return card;
  }

  // After a rewind the conversation ends on a line that already has answers.
  function branchesCard(answers) {
    const card = el("div", "card branches");
    card.append(
      el("div", "label", "Rewound to here"),
      el("p", "", "Type a different answer, or go back to one you gave before:"),
    );
    const choices = el("div", "choices");
    for (const answer of answers) {
      const button = el("button", "secondary", answer.text);
      button.type = "button";
      button.addEventListener("click", () => handlers.onShowBranch(answer));
      choices.append(button);
    }
    card.append(choices);
    return card;
  }

  // What follows the last line: earlier answers after a rewind, the summary at the end.
  function renderTail(tree) {
    chat.querySelector(".tail")?.remove();
    for (const bubble of chat.querySelectorAll(".msg.tutor")) {
      bubble.classList.toggle("current", bubble.dataset.id === tree.active.id);
    }
    const tail = el("div", "tail");
    const answers = tree.childrenOf(tree.active.id);
    if (answers.length) tail.append(branchesCard(answers));
    if (tree.done) tail.append(summaryCard(tree));
    if (tail.children.length) chat.append(tail);
  }

  return {
    scrollDown,
    renderTail,

    // Draw the shown conversation from scratch.
    renderPath(tree) {
      chat.replaceChildren();
      for (const node of tree.activePath) chat.append(...line(tree, node));
      renderTail(tree);
      scrollDown();
    },

    // Add lines at the end, keeping the failed attempts above them on screen.
    appendLines(tree, nodes) {
      chat.querySelector(".tail")?.remove();
      for (const node of nodes) chat.append(...line(tree, node));
      renderTail(tree);
    },

    // The learner's message while the model is judging it.
    addAttempt(text) {
      chat.querySelector(".tail")?.remove();
      const attempt = el("div", "msg learner pending");
      attempt.append(el("p", "", text));
      chat.append(attempt);
      return attempt;
    },

    // The message did not pass: strike it through and show how to say it.
    addCorrection(attempt, result, language) {
      attempt.classList.replace("pending", "retry");
      const card = el("div", `card ${result.verdict}`);
      card.append(el("div", "label", CORRECTION_LABELS[result.verdict](language)));
      if (result.ideal) {
        const ideal = el("div", "line");
        ideal.append(el("span", "ideal", result.ideal), speakButton(result.ideal));
        card.append(ideal);
      }
      if (result.alternatives.length) {
        const list = el("ul");
        for (const alternative of result.alternatives) {
          const item = el("li", "line");
          item.append(el("span", "", alternative), speakButton(alternative));
          list.append(item);
        }
        card.append(list);
      }
      if (result.explanation) card.append(el("p", "explanation", result.explanation));
      card.append(el("p", "next", `Now say it in ${language}.`));
      chat.append(card);
    },

    setThinking(thinking) {
      chat.querySelector(".thinking")?.remove();
      if (thinking) {
        chat.append(el("div", "thinking", "Thinking"));
        scrollDown();
      }
    },
  };
}
