import { reactive } from "vue";

import {
  deleteAllSettings,
  fetchAllSettings,
  putNamespace,
  type SettingsMap,
} from "../api/settings";

const CACHE_KEY = "openvoca.settings.cache";

/**
 * Provider keys served only by the dedicated provider API.
 *
 * They may carry credentials (the API key, session headers), so generic
 * settings paths must skip them when caching, exporting and importing.
 * Keeping one definition here stops the three call sites from drifting apart.
 */
const PROVIDER_SENSITIVE_KEYS = new Set(["apiKey", "headers"]);

function isProviderSensitive(namespace: string, key: string): boolean {
  return namespace === "provider" && PROVIDER_SENSITIVE_KEYS.has(key);
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
      if (isProviderSensitive(ns, k)) continue;
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
 * Excludes sensitive provider keys to prevent accidental leakage.
 */
function exportAll(): SettingsMap {
  const snapshot: SettingsMap = {};
  for (const [ns, entries] of Object.entries(store)) {
    const filtered: Record<string, string> = {};
    for (const [k, v] of Object.entries(entries)) {
      if (isProviderSensitive(ns, k)) continue;
      filtered[k] = v;
    }
    if (Object.keys(filtered).length > 0) {
      snapshot[ns] = filtered;
    }
  }
  return snapshot;
}

/**
 * Import settings from a JSON map. Merges into existing settings.
 * Sensitive provider keys are silently skipped.
 * Persists each namespace to the backend and updates localStorage.
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
      if (isProviderSensitive(ns, k)) continue;
      filtered[k] = v;
    }
    if (Object.keys(filtered).length === 0) continue;
    if (!store[ns]) store[ns] = {};
    for (const [k, v] of Object.entries(filtered)) {
      store[ns][k] = v;
    }
    await putNamespace(ns, filtered).catch(() => {});
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
