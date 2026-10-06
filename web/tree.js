// A conversation as a tree of lines.
//
// Tutor and learner lines alternate. Rewinding and answering differently, or
// asking for another reply, adds a sibling instead of replacing a line, so no
// branch is ever lost. The tree always ends on a tutor line, `active`: the path
// from the root to it is the conversation that is shown.
//
// This module knows nothing about the page or the server.

export class ConversationTree {
  // `doc` is the conversation as it is saved:
  // {id, title, scenario, situation, target_language, level, voice, created, nodes, active}
  // with nodes [{id, parent, role, text, translation, typed, note, done, pick}].
  constructor(doc) {
    this.doc = doc;
    if (!this.active) this.activate(this.leafOf(doc.nodes[0]));
  }

  // A new conversation that starts with the tutor's opening line.
  static start({ id, scenario, situation, targetLanguage, level, voice, created, text, translation }) {
    const doc = {
      id,
      title: scenario.title,
      scenario,
      situation,
      target_language: targetLanguage,
      level,
      voice,
      created,
      nodes: [{ id: "n1", parent: null, role: "tutor", text, translation }],
      active: "n1",
    };
    return new ConversationTree(doc);
  }

  get id() { return this.doc.id; }
  get title() { return this.doc.title; }
  get scenario() { return this.doc.scenario; }
  get situation() { return this.doc.situation; }
  // The language, level and voice the conversation was started with. It keeps
  // them, whatever is set in Settings later. Level and voice are missing in
  // conversations saved before they were recorded.
  get targetLanguage() { return this.doc.target_language; }
  get level() { return this.doc.level || null; }
  get voice() { return this.doc.voice || null; }

  node(id) {
    return this.doc.nodes.find((node) => node.id === id);
  }

  // The lines that answer the line with this id; null gives the opening lines.
  childrenOf(id) {
    return this.doc.nodes.filter((node) => node.parent === id);
  }

  // The versions of one turn: the node itself and its alternatives, oldest first.
  siblingsOf(node) {
    return this.childrenOf(node.parent);
  }

  // The lines from the opening down to `node`. Without a node: no lines.
  pathTo(node) {
    const path = [];
    for (; node; node = this.node(node.parent)) path.unshift(node);
    return path;
  }

  // The tutor line the shown conversation ends on.
  get active() {
    return this.node(this.doc.active);
  }

  get activePath() {
    return this.pathTo(this.active);
  }

  // True when the shown conversation has reached the end of the scene.
  get done() {
    return Boolean(this.active.done);
  }

  // The learner's accepted answer to a tutor line. `text` is the corrected
  // form, `typed` what they wrote.
  addLearnerLine(tutorNode, { text, typed, note }) {
    return this.#add({ parent: tutorNode.id, role: "learner", text, typed, note });
  }

  // A tutor line answering a learner line, or another opening line if there is none.
  addTutorLine(learnerNode, { text, translation, done }) {
    return this.#add({ parent: learnerNode ? learnerNode.id : null, role: "tutor", text, translation, done });
  }

  #add(fields) {
    // nodes are never removed, so the count gives a fresh id
    const node = { id: `n${this.doc.nodes.length + 1}`, ...fields };
    this.doc.nodes.push(node);
    return node;
  }

  // The end of the branch through `node`, following the line that was shown last.
  leafOf(node) {
    for (;;) {
      const children = this.childrenOf(node.id);
      if (!children.length) return node;
      node = children.find((child) => child.id === node.pick) || children[children.length - 1];
    }
  }

  // Make `node` the end of the shown conversation and remember the way to it.
  activate(node) {
    for (let child = node, parent = this.node(child.parent); parent; child = parent, parent = this.node(parent.parent)) {
      parent.pick = child.id;
    }
    this.doc.active = node.id;
  }

  // Show the branch through `node`, continued to where it was left.
  showBranch(node) {
    this.activate(this.leafOf(node));
  }

  toJSON() {
    return this.doc;
  }
}
