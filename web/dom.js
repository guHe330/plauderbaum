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

let toastTimer;
export function toast(message, isError = false) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.toggle("error", isError);
  node.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.hidden = true; }, isError ? 7000 : 2500);
}
