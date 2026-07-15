/*
 * Client-side settings loader. Turns an uploaded file into a flat {name: value} object
 * for the Python validator. Two formats, both handled in the browser (nothing leaves it):
 *   - AAPS encrypted prefs (.json, security.algorithm "v1") -> WebCrypto decrypt with the
 *     master password (aaps_prefs.mjs). "none" = unencrypted AAPS export.
 *   - Trio / oref preferences (plain JSON, e.g. {"max_iob":6,...}) -> parse + flatten.
 */
import { decryptAapsPrefs } from './aaps_prefs.mjs';

function flatten(obj, out = {}) {
  for (const [k, v] of Object.entries(obj || {})) {
    if (v !== null && typeof v === 'object' && !Array.isArray(v)) flatten(v, out);
    else out[k] = v;
  }
  return out;
}

function isAapsEncrypted(obj) {
  return obj && obj.security && obj.security.algorithm === 'v1';
}
function isAapsUnencrypted(obj) {
  return obj && obj.security && obj.security.algorithm === 'none' && obj.content;
}

/**
 * @returns {Promise<{raw?: object, format: string, needsPassword?: boolean}>}
 */
export async function loadSettingsFromFile(file, password) {
  const text = await file.text();
  let obj;
  try {
    obj = JSON.parse(text);
  } catch {
    throw new Error('That file is not valid JSON. Upload an AAPS prefs export or a Trio settings JSON.');
  }

  if (isAapsEncrypted(obj)) {
    if (!password) return { format: 'aaps-encrypted', needsPassword: true };
    const content = await decryptAapsPrefs(text, password);   // throws on wrong password
    return { raw: flatten(content), format: 'aaps-encrypted' };
  }
  if (isAapsUnencrypted(obj)) {
    const content = await decryptAapsPrefs(text, '');         // returns content.content directly
    return { raw: flatten(content), format: 'aaps' };
  }
  // Trio / oref preferences, or any plain settings JSON.
  return { raw: flatten(obj), format: 'trio/plain' };
}
