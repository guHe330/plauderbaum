// What the page knows at the moment. Everything lasting is on the server.
export const state = {
  settings: {},    // as sent by /api/settings, without the API keys
  languages: {},   // language code -> name
  tree: null,      // the open conversation, a ConversationTree
  busy: false,     // true while waiting for the model
};

export function targetName() {
  return state.languages[state.settings.target_language] || "the language";
}
