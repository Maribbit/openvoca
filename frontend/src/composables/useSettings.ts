import { reactive } from "vue";

import {
  deleteAllSettings,
  fetchAllSettings,
  putNamespace,
  setProvider,
  type SettingsMap,
} from "../api/settings";

const CACHE_KEY = "openvoca.settings.cache";
const PROVIDER_NAMESPACE = "provider";

/**
 * Provider keys the client is never given, so no client-side path can move them.
 *
 * The API key is written through its own endpoint and read back as a boolean
 * plus a hint, so there is no value here to cache, export or import. Listing it
 * keeps the three paths agreeing with the server about what is not theirs.
 */
const PROVIDER_UNREADABLE_KEYS = new Set(["apiKey"]);

/**
 * Provider keys that may hold a credential, and so stay out of the automatic
 * cache.
 *
 * Custom headers exist partly to express non-Bearer auth schemes -- x-api-key
 * and the like -- so a header value can be a credential. The cache is written
 * on every change without being asked and localStorage is readable by any
 * script on the origin, which is a different proposition from a file the user
 * chose to download.
 *
 * Export is therefore allowed to carry these and the cache is not: an automatic
 * copy and an explicit backup are not the same thing.
 */
const PROVIDER_CREDENTIAL_KEYS = new Set(["apiKey", "headers"]);

function isUnreadableProviderKey(namespace: string, key: string): boolean {
  return namespace === PROVIDER_NAMESPACE && PROVIDER_UNREADABLE_KEYS.has(key);
}

function isCredentialProviderKey(namespace: string, key: string): boolean {
  return namespace === PROVIDER_NAMESPACE && PROVIDER_CREDENTIAL_KEYS.has(key);
}

/**
 * Read a JSON object out of a settings value.
 *
 * Returns null when the value is absent, unparseable, or not an object -- as
 * distinct from an empty object, which is a legitimate "nothing configured".
 * The difference matters on import: treating a corrupt value as empty would
 * silently clear a working configuration, which is the kind of data loss a
 * backup exists to prevent.
 */
function parseJsonObject(raw: string): Record<string, unknown> | null {
  try {
    const parsed: unknown = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    // A value that is not JSON is not a set of fields.
  }
  return null;
}

/** Header values must be strings; anything else would be rejected on write. */
function parseHeaders(raw: string): Record<string, string> | null {
  const parsed = parseJsonObject(raw);
  if (parsed === null) return null;
  return Object.fromEntries(
    Object.entries(parsed).filter(([, value]) => typeof value === "string"),
  ) as Record<string, string>;
}

/** Flat reactive store: settings[namespace][key] = value */
const store = reactive<SettingsMap>({});

let hydrated = false;

// --- localStorage cache ---

function loadCache(): SettingsMap {
  if (typeof window === "undefined") return {};
  const raw = window.localStorage.getItem(CACHE_KEY);
  if (!raw) return {};
  try {
    return JSON.parse(raw) as SettingsMap;
  } catch {
    return {};
  }
}

function saveCache(): void {
  if (typeof window === "undefined") return;
  // Strip sensitive keys before persisting to localStorage
  const safe: SettingsMap = {};
  for (const [ns, entries] of Object.entries(store)) {
    const filtered: Record<string, string> = {};
    for (const [k, v] of Object.entries(entries)) {
      if (isCredentialProviderKey(ns, k)) continue;
      filtered[k] = v;
    }
    if (Object.keys(filtered).length > 0) {
      safe[ns] = filtered;
    }
  }
  window.localStorage.setItem(CACHE_KEY, JSON.stringify(safe));
}

function applyMap(map: SettingsMap): void {
  for (const [ns, entries] of Object.entries(map)) {
    if (!store[ns]) store[ns] = {};
    for (const [k, v] of Object.entries(entries)) {
      store[ns][k] = v;
    }
  }
}

applyMap(loadCache());

// --- Public API ---

/** Read a single setting. Returns `fallback` when the key is absent. */
function get(namespace: string, key: string, fallback = ""): string {
  return store[namespace]?.[key] ?? fallback;
}

/** Return all key-value pairs in a namespace. */
function getNamespace(namespace: string): Record<string, string> {
  return store[namespace] ?? {};
}

/**
 * Write one or more keys in a namespace.
 * Updates local reactive store + localStorage cache immediately,
 * then persists to the backend asynchronously.
 */
function set(namespace: string, entries: Record<string, string>): void {
  if (!store[namespace]) store[namespace] = {};
  for (const [k, v] of Object.entries(entries)) {
    store[namespace][k] = v;
  }
  saveCache();
  putNamespace(namespace, entries).catch(() => {
    // Silently ignore network errors — cache is the source of truth for now
  });
}

/**
 * Hydrate the store: load localStorage cache first (sync),
 * then fetch from API and merge (async).
 * Safe to call multiple times — only the first call fetches.
 */
async function hydrate(): Promise<void> {
  if (hydrated) return;
  hydrated = true;

  // Instant: populate from cache
  applyMap(loadCache());

  // Background: sync from server
  try {
    const remote = await fetchAllSettings();
    applyMap(remote);
    saveCache();
  } catch {
    // Offline or backend unreachable — cache is enough
  }
}

export function useSettings() {
  return {
    store,
    get,
    getNamespace,
    set,
    hydrate,
    clearAll,
    exportAll,
    importAll,
    _reset,
  };
}

/**
 * Clear all settings: wipe reactive store, localStorage cache, and backend.
 */
async function clearAll(): Promise<void> {
  for (const key of Object.keys(store)) {
    delete store[key];
  }
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(CACHE_KEY);
  }
  await deleteAllSettings().catch(() => {});
}

/**
 * Export all settings as a JSON-serializable map.
 *
 * The API key is the only exclusion, and it is absent because the client never
 * holds it. Everything else travels, custom headers included: a backup that
 * silently omits part of the configuration is worse than none, because it gives
 * the confidence of a backup without being one.
 */
function exportAll(): SettingsMap {
  const snapshot: SettingsMap = {};
  for (const [ns, entries] of Object.entries(store)) {
    const filtered: Record<string, string> = {};
    for (const [k, v] of Object.entries(entries)) {
      if (isUnreadableProviderKey(ns, k)) continue;
      filtered[k] = v;
    }
    if (Object.keys(filtered).length > 0) {
      snapshot[ns] = filtered;
    }
  }
  return snapshot;
}

/**
 * Write an imported provider configuration through its own API.
 *
 * The generic settings write refuses this namespace, and rightly so: provider
 * configuration has a write path that also rebuilds the live client, and a
 * generic write would leave the runtime serving the previous configuration.
 * Routing the import here honours that rather than weakening the refusal.
 *
 * Only the keys the file carries are sent. An absent field takes the server's
 * default rather than being overwritten with an empty value.
 */
async function importProviderNamespace(
  entries: Record<string, string>,
): Promise<void> {
  const config: Record<string, unknown> = {};
  if (entries.endpoint) config.endpoint = entries.endpoint;
  if (entries.model) config.model = entries.model;
  if (entries.headers) {
    const headers = parseHeaders(entries.headers);
    if (headers) config.headers = headers;
  }
  if (entries.bodyFields) {
    const fields = parseJsonObject(entries.bodyFields);
    if (fields) config.bodyFields = fields;
  }
  if (Object.keys(config).length === 0) return;
  await setProvider(config);
}

/**
 * Import settings from a JSON map. Merges into existing settings.
 * The API key is skipped: the file does not carry it, and the client cannot
 * supply one it never had.
 * Persists each namespace through its own write path and updates localStorage.
 */
async function importAll(data: SettingsMap): Promise<void> {
  for (const [ns, entries] of Object.entries(data)) {
    if (
      typeof entries !== "object" ||
      entries === null ||
      Array.isArray(entries)
    )
      continue;
    const filtered: Record<string, string> = {};
    for (const [k, v] of Object.entries(entries)) {
      if (typeof v !== "string") continue;
      if (isUnreadableProviderKey(ns, k)) continue;
      filtered[k] = v;
    }
    if (Object.keys(filtered).length === 0) continue;
    if (!store[ns]) store[ns] = {};
    for (const [k, v] of Object.entries(filtered)) {
      store[ns][k] = v;
    }
    if (ns === PROVIDER_NAMESPACE) {
      await importProviderNamespace(filtered).catch(() => {});
    } else {
      await putNamespace(ns, filtered).catch(() => {});
    }
  }
  saveCache();
}

/** Reset the store for test isolation. */
function _reset(): void {
  for (const key of Object.keys(store)) {
    delete store[key];
  }
  hydrated = false;
}
