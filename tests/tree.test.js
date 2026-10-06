// Run with: node --test
import assert from "node:assert/strict";
import { test } from "node:test";

import { ConversationTree } from "../web/tree.js";

function start() {
  return ConversationTree.start({
    id: "11111111-1111-1111-1111-111111111111",
    scenario: { title: "Bakery", brief: "The tutor plays the baker." },
    situation: "You are at a bakery.",
    targetLanguage: "it",
    level: "A2",
    voice: "it-IT-IsabellaNeural",
    created: "2026-10-05T10:00:00.000Z",
    text: "Buongiorno!",
    translation: "Good morning!",
  });
}

// One accepted learner answer and the tutor's reply to it, made the shown end.
function exchange(tree, tutorNode, said, reply, done = false) {
  const learner = tree.addLearnerLine(tutorNode, { text: said, typed: said.toLowerCase(), note: "" });
  const tutor = tree.addTutorLine(learner, { text: reply, translation: "", done });
  tree.activate(tutor);
  return [learner, tutor];
}

const texts = (nodes) => nodes.map((node) => node.text);

test("a new conversation ends on the opening line", () => {
  const tree = start();
  assert.deepEqual(texts(tree.activePath), ["Buongiorno!"]);
  assert.equal(tree.title, "Bakery");
  assert.equal(tree.targetLanguage, "it");
  assert.equal(tree.level, "A2");
  assert.equal(tree.voice, "it-IT-IsabellaNeural");
  assert.equal(tree.done, false);
});

test("exchanges extend the shown path", () => {
  const tree = start();
  const [, baker] = exchange(tree, tree.active, "Un pane.", "Quale?");
  exchange(tree, baker, "Integrale.", "Ecco. Arrivederci!", true);
  assert.deepEqual(texts(tree.activePath), ["Buongiorno!", "Un pane.", "Quale?", "Integrale.", "Ecco. Arrivederci!"]);
  assert.equal(tree.done, true);
});

test("rewinding and answering differently keeps the earlier branch", () => {
  const tree = start();
  const opening = tree.active;
  const [bread] = exchange(tree, opening, "Un pane.", "Quale?");

  tree.activate(opening);
  assert.deepEqual(texts(tree.activePath), ["Buongiorno!"]);
  assert.deepEqual(texts(tree.childrenOf(opening.id)), ["Un pane."]);

  const [cake] = exchange(tree, opening, "Una torta.", "Certo!");
  assert.deepEqual(texts(tree.activePath), ["Buongiorno!", "Una torta.", "Certo!"]);
  assert.deepEqual(tree.siblingsOf(cake), [bread, cake]);

  tree.showBranch(bread);
  assert.deepEqual(texts(tree.activePath), ["Buongiorno!", "Un pane.", "Quale?"]);
});

test("switching back to a branch continues where it was left", () => {
  const tree = start();
  const opening = tree.active;
  const [bread, which] = exchange(tree, opening, "Un pane.", "Quale?");
  exchange(tree, which, "Integrale.", "Ecco.");
  tree.activate(which);
  exchange(tree, which, "Bianco.", "Subito.");   // last shown below "Quale?"
  const [cake] = exchange(tree, opening, "Una torta.", "Certo!");

  tree.showBranch(bread);
  assert.deepEqual(texts(tree.activePath), ["Buongiorno!", "Un pane.", "Quale?", "Bianco.", "Subito."]);
  tree.showBranch(cake);
  assert.deepEqual(texts(tree.activePath), ["Buongiorno!", "Una torta.", "Certo!"]);
});

test("another reply becomes a sibling of the tutor line", () => {
  const tree = start();
  const [learner, first] = exchange(tree, tree.active, "Un pane.", "Quale?");
  const second = tree.addTutorLine(learner, { text: "Il pane è finito.", translation: "", done: false });
  tree.activate(second);
  assert.deepEqual(tree.siblingsOf(second), [first, second]);
  assert.deepEqual(texts(tree.activePath), ["Buongiorno!", "Un pane.", "Il pane è finito."]);
});

test("another opening line is a second root", () => {
  const tree = start();
  const first = tree.active;
  const second = tree.addTutorLine(undefined, { text: "Buonasera!", translation: "", done: false });
  tree.activate(second);
  assert.equal(second.parent, null);
  assert.deepEqual(tree.siblingsOf(second), [first, second]);
  assert.deepEqual(texts(tree.activePath), ["Buonasera!"]);
  assert.deepEqual(tree.pathTo(undefined), []);
});

test("node ids stay unique across branches", () => {
  const tree = start();
  const opening = tree.active;
  exchange(tree, opening, "Un pane.", "Quale?");
  exchange(tree, opening, "Una torta.", "Certo!");
  const ids = tree.doc.nodes.map((node) => node.id);
  assert.equal(new Set(ids).size, ids.length);
});

test("a saved tree comes back as it was", () => {
  const tree = start();
  const opening = tree.active;
  const [bread] = exchange(tree, opening, "Un pane.", "Quale?");
  exchange(tree, opening, "Una torta.", "Certo!");
  tree.showBranch(bread);

  const reopened = new ConversationTree(JSON.parse(JSON.stringify(tree)));
  assert.deepEqual(texts(reopened.activePath), ["Buongiorno!", "Un pane.", "Quale?"]);
  assert.equal(reopened.id, tree.id);
});

test("a tree saved before level and voice were recorded has neither", () => {
  const doc = JSON.parse(JSON.stringify(start()));
  delete doc.level;
  doc.voice = "";
  const tree = new ConversationTree(doc);
  assert.equal(tree.level, null);
  assert.equal(tree.voice, null);
  assert.equal(tree.targetLanguage, "it");
});

test("a saved tree without a usable end opens on its last branch", () => {
  const tree = start();
  exchange(tree, tree.active, "Un pane.", "Quale?");
  const doc = JSON.parse(JSON.stringify(tree));
  doc.active = "gone";
  assert.deepEqual(texts(new ConversationTree(doc).activePath), ["Buongiorno!", "Un pane.", "Quale?"]);
});
