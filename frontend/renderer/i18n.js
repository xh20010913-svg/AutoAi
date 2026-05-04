// i18n — lightweight internationalization module
const I18N_KEY = "autoai_lang";

let _lang = localStorage.getItem(I18N_KEY) || "en";
let _dict = {};
const _listeners = [];

async function loadLang(lang) {
  const resp = await fetch(lang + ".json");
  _dict = await resp.json();
  _lang = lang;
  localStorage.setItem(I18N_KEY, lang);
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  _listeners.forEach((fn) => fn(lang));
}

// dot-path lookup: t("sidebar.board") → _dict.sidebar.board
function t(key, params) {
  const parts = key.split(".");
  let val = _dict;
  for (const p of parts) {
    if (val == null) return key;
    val = val[p];
  }
  if (typeof val !== "string") return key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      val = val.replace("{" + k + "}", v);
    }
  }
  return val;
}

function getLang() {
  return _lang;
}

function onLangChange(fn) {
  _listeners.push(fn);
}

// Apply data-i18n attributes to static HTML elements
function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    el.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    el.placeholder = t(key);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    const key = el.getAttribute("data-i18n-title");
    el.title = t(key);
  });
}

// Initialize: load the language file, then notify listeners
async function initI18n() {
  await loadLang(_lang);
  applyTranslations();
}
