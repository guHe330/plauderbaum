// Small helpers for building and finding elements.
export const $ = (selector) => document.querySelector(selector);

export function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function linkButton(label, onClick, className = "") {
  const button = el("button", `link ${className}`.trim(), label);
  button.type = "button";
  button.addEventListener("click", onClick);
  return button;
}

// Ask in a dialog of our own. `choices` are {label, value, className}, the last
// one the main action; the first gets the focus, so put the safe one there.
// Resolves to the value of the chosen button, or "" for Escape.
export function ask(message, choices) {
  const dialog = $("#ask");
  $("#ask-message").textContent = message;
  $("#ask-buttons").replaceChildren(...choices.map(({ label, value, className }) => {
    const button = el("button", className, label);
    button.value = value;
    return button;
  }));
  dialog.returnValue = "";
  dialog.showModal();
  return new Promise((resolve) => {
    dialog.addEventListener("close", () => resolve(dialog.returnValue), { once: true });
  });
}

let toastTimer;
export function toast(message, isError = false) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.toggle("error", isError);
  node.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.hidden = true; }, isError ? 7000 : 2500);
}
