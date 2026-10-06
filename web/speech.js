// Reads lines aloud, one after the other, with the voice chosen in Settings.
import { linkButton, toast } from "./dom.js";
import { state } from "./state.js";

const player = new Audio();
const queue = [];   // lines waiting to be spoken: {text, voice}
let speaking = false;
// The voice of the open conversation, if it is in another language than the
// one set in Settings. Otherwise null, and the voice from Settings is used.
let conversationVoice = null;

export function setConversationVoice(voice) {
  conversationVoice = voice;
}

function playNext() {
  const line = queue.shift();
  if (line === undefined) { speaking = false; return; }
  speaking = true;
  // the rate is in the URL only so a changed setting is not served from cache
  const query = new URLSearchParams({ text: line.text, voice: line.voice, r: state.settings.speech_rate });
  player.src = `/api/tts?${query}`;
  player.play().catch(() => { speaking = false; });
}
player.addEventListener("ended", playNext);
player.addEventListener("error", () => {
  toast("The voice service did not answer.", true);
  playNext();
});

// Say these lines now, dropping whatever was queued. Without lines: be quiet.
export function say(...texts) {
  sayIn(conversationVoice || state.settings.voice, ...texts);
}

// The same in a given voice, for trying out the one chosen in Settings.
export function sayIn(voice, ...texts) {
  queue.length = 0;
  if (!texts.length) player.pause();
  queue.push(...texts.filter(Boolean).map((text) => ({ text, voice })));
  playNext();
}

// Say a new tutor line after what is already playing, if the learner wants that.
export function autoSay(text) {
  if (!state.settings.auto_speak || !text) return;
  queue.push({ text, voice: conversationVoice || state.settings.voice });
  if (!speaking) playNext();
}

export function speakButton(text) {
  return linkButton("🔊 Listen", () => say(text));
}
