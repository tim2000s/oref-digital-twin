/*
 * Client-side settings loader. Turns an uploaded file into a flat {name: value} object
 * for the Python validator. Three formats, all handled in the browser (nothing leaves it):
 *   - AAPS encrypted prefs (.json, security.algorithm "v1") -> WebCrypto decrypt with the
 *     master password (aaps_prefs.mjs). "none" = unencrypted AAPS export.
 *   - Trio's Export Settings file (.csv of screen labels) -> the rows the validator knows,
 *     under their oref names.
 *   - oref preferences (plain JSON, e.g. {"max_iob":6,...}) -> parse + flatten.
 */
import { decryptAapsPrefs } from './aaps_prefs.mjs';

// Nested sections are flattened onto one namespace, so the same leaf key can appear twice
// with different values. Last-wins silently would let the wrong insulin-relevant number
// through, so collisions are collected and reported rather than swallowed.
function flatten(obj, out = {}, collisions = new Set()) {
  for (const [k, v] of Object.entries(obj || {})) {
    if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
      flatten(v, out, collisions);
    } else {
      if (Object.prototype.hasOwnProperty.call(out, k) && out[k] !== v) collisions.add(k);
      out[k] = v;
    }
  }
  return out;
}

function flattenWithCollisions(obj) {
  const collisions = new Set();
  const raw = flatten(obj, {}, collisions);
  return { raw, collisions: [...collisions] };
}

function isAapsEncrypted(obj) {
  return obj && obj.security && obj.security.algorithm === 'v1';
}
function isAapsUnencrypted(obj) {
  return obj && obj.security && obj.security.algorithm === 'none' && obj.content;
}

// Trio's Settings > Trio Backup > Export Settings writes one row per setting, named by its
// screen label (SettingsExportStateModel.swift in Trio). These are the labels of the settings
// the validator knows, with the names Trio's own preferences give them.
const TRIO_EXPORT_HEADER = 'Setting Category,Subcategory,Setting Name,Value,Unit';
const TRIO_EXPORT_NAMES = {
  'Maximum Insulin on Board (IOB)': 'max_iob',
  'Maximum Basal Rate': 'max_basal',
  'Maximum Carbs on Board (COB)': 'maxCOB',
  'Autosens Max': 'autosens_max',
  'Autosens Min': 'autosens_min',
  'Enable SMB Always': 'enableSMB_always',
  'Enable SMB With COB': 'enableSMB_with_COB',
  'Enable SMB With Temptarget': 'enableSMB_with_temptarget',
  'Enable SMB After Carbs': 'enableSMB_after_carbs',
  'Enable SMB With High Glucose': 'enableSMB_high_bg',
  'High Glucose Target': 'enableSMB_high_bg_target',
  'Allow SMB With High Temptarget': 'allowSMB_with_high_temptarget',
  'Enable UAM': 'enableUAM',
  'Max SMB Basal Minutes': 'maxSMBBasalMinutes',
  'Max UAM Basal Minutes': 'maxUAMSMBBasalMinutes',
  'Dynamic ISF': 'useNewFormula',
  'Max Daily Safety Multiplier': 'max_daily_safety_multiplier',
  'Current Basal Safety Multiplier': 'current_basal_safety_multiplier',
  'Use Custom Peak Time': 'useCustomPeakTime',
  'Insulin Peak Time': 'insulinPeakTime',
  'SMB Delivery Ratio': 'smb_delivery_ratio',
};
const TRIO_EXPORT_WORDS = { Enabled: true, Disabled: false, Sigmoid: true, Logarithmic: true };
const MGDL_PER_MMOL = 18.0182;

// shortcut: English exports only, since Trio writes labels and values in the app's language;
// add the other languages when someone reports "No recognised settings" from a translated file.
function trioExportToRaw(text) {
  const raw = {};
  const collisions = new Set();
  const unread = [];
  let row = [];
  for (const m of text.matchAll(/(?:"((?:[^"]|"")*)"|([^,\r\n]*))(,|\r?\n|$)/g)) {
    row.push(m[1] !== undefined ? m[1].replace(/""/g, '"') : m[2]);
    if (m[3] === ',') continue;
    const [category, , name, value, unit] = row;
    row = [];
    // The preset categories reuse names such as "Target" for other things.
    if ((category !== 'Therapy' && category !== 'Algorithm') || !Object.hasOwn(TRIO_EXPORT_NAMES, name)) continue;
    let v;
    if (Object.hasOwn(TRIO_EXPORT_WORDS, value)) {
      v = TRIO_EXPORT_WORDS[value];
    } else if (value === '' || !Number.isFinite(Number(value))) {
      // Anything else (a value Trio annotates as overridden by the dosing mode, or a word in
      // another language) is left out and named: the validator would read an unknown word as "off".
      unread.push(name);
      continue;
    } else {
      // oref holds percentages as fractions and glucose in mg/dL.
      v = unit === '%' ? value / 100 : unit === 'mmol/L' ? value * MGDL_PER_MMOL : Number(value);
    }
    const key = TRIO_EXPORT_NAMES[name];
    if (Object.hasOwn(raw, key) && raw[key] !== v) collisions.add(key);
    raw[key] = v;
  }
  return { raw, collisions: [...collisions], unread };
}

/**
 * @returns {Promise<{raw?: object, format: string, needsPassword?: boolean, unread?: string[]}>}
 */
export async function loadSettingsFromFile(file, password) {
  const text = (await file.text()).replace(/^\uFEFF/, '');
  if (text.startsWith(TRIO_EXPORT_HEADER)) return { ...trioExportToRaw(text), format: 'Trio export' };
  let obj;
  try {
    obj = JSON.parse(text);
  } catch {
    throw new Error('That file is neither an AAPS preferences export nor a Trio settings export.');
  }

  if (isAapsEncrypted(obj)) {
    if (!password) return { format: 'aaps-encrypted', needsPassword: true };
    const content = await decryptAapsPrefs(text, password);   // throws on wrong password
    return { ...flattenWithCollisions(content), format: 'aaps-encrypted' };
  }
  if (isAapsUnencrypted(obj)) {
    const content = await decryptAapsPrefs(text, '');         // returns content.content directly
    return { ...flattenWithCollisions(content), format: 'aaps' };
  }
  // oref preferences, or any plain settings JSON.
  return { ...flattenWithCollisions(obj), format: 'plain JSON' };
}
