// One call to the local server. Errors carry a message fit to show to the learner.
export async function api(path, body, method) {
  const options = { method: method || (body === undefined ? "GET" : "POST") };
  if (body !== undefined) {
    options.headers = { "Content-Type": "application/json" };
    options.body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new Error("The app is not running any more. Start it again.");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `Request failed (${response.status}).`);
  }
  return data;
}
