// Saved conversations on the server.
import { api } from "./api.js";
import { toast } from "./dom.js";
import { ConversationTree } from "./tree.js";

let saving = Promise.resolve();

// Save the tree as it is now. Saves go out one at a time, in order, so an
// older tree can never overwrite a newer one.
export function saveConversation(tree) {
  const snapshot = JSON.parse(JSON.stringify(tree));
  saving = saving
    .then(() => api(`/api/conversations/${snapshot.id}`, snapshot, "PUT"))
    .catch((error) => toast(`Not saved: ${error.message}`, true));
}

// Summaries of all saved conversations, most recently used first.
export async function listConversations() {
  // wait for a save that is still on its way, so the list is up to date
  await saving;
  return api("/api/conversations");
}

export async function loadConversation(id) {
  return new ConversationTree(await api(`/api/conversations/${id}`));
}

export function deleteConversation(id) {
  return api(`/api/conversations/${id}`, undefined, "DELETE");
}
