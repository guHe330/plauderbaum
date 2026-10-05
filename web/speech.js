// Reads lines aloud, one after the other, with the voice chosen in Settings.
import { linkButton, toast } from "./dom.js";
import { state } from "./state.js";

const player = new Audio();
const queue = [];
let speaking = false;

function playNext() {
  const text = queue.shift();
  if (text === undefined) { speaking = false; return; }
  speaking = true;
  // voice and rate are in the URL only so a changed setting is not served from cache
  const query = new URLSearchParams({ text, v: state.settings.voice, r: state.settings.speech_rate });
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
  queue.length = 0;
  if (!texts.length) player.pause();
  queue.push(...texts.filter(Boolean));
  playNext();
}

// Say a new tutor line after what is already playing, if the learner wants that.
export function autoSay(text) {
  if (!state.settings.auto_speak || !text) return;
  queue.push(text);
  if (!speaking) playNext();
}

export function speakButton(text) {
  return linkButton("🔊 Listen", () => say(text));
}
