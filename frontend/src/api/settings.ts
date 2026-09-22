export type SettingsMap = Record<string, Record<string, string>>;

export async function fetchAllSettings(): Promise<SettingsMap> {
  const response = await fetch("/api/settings", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error("Failed to fetch settings.");
  return (await response.json()) as SettingsMap;
}

export async function fetchNamespace(
  namespace: string,
): Promise<Record<string, string>> {
  const response = await fetch(
    `/api/settings/${encodeURIComponent(namespace)}`,
    {
      headers: { Accept: "application/json" },
    },
  );
  if (!response.ok) throw new Error(`Failed to fetch settings/${namespace}.`);
  return (await response.json()) as Record<string, string>;
}

export async function putSetting(
  namespace: string,
  key: string,
  value: string,
): Promise<void> {
  const response = await fetch(
    `/api/settings/${encodeURIComponent(namespace)}/${encodeURIComponent(key)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    },
  );
  if (!response.ok)
    throw new Error(`Failed to save setting ${namespace}/${key}.`);
}

export async function putNamespace(
  namespace: string,
  settings: Record<string, string>,
): Promise<void> {
  const response = await fetch(
    `/api/settings/${encodeURIComponent(namespace)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    },
  );
  if (!response.ok) throw new Error(`Failed to save settings/${namespace}.`);
}

export async function deleteAllSettings(): Promise<number> {
  const response = await fetch("/api/settings", { method: "DELETE" });
  if (!response.ok) throw new Error("Failed to clear settings.");
  const data = (await response.json()) as { deleted: number };
  return data.deleted;
}

export interface ProviderState {
  endpoint: string;
  model: string;
  /** Custom request headers, returned in full so they can be edited. */
  headers: Record<string, string>;
  /**
   * Extra request body fields, returned in full so they can be edited.
   *
   * Values are unknown rather than string: providers that control reasoning use
   * flat strings, nested objects and booleans, and coercing any of them would
   * change what the provider reads.
   */
  bodyFields: Record<string, unknown>;
  /** Whether a key is stored. The key itself is never sent to the client. */
  apiKeySet: boolean;
  /** Irreversible fragment for display only; must never be sent back. */
  apiKeyHint: string;
}

export interface ProviderConfig {
  endpoint: string;
  model: string;
  headers: Record<string, string>;
  bodyFields: Record<string, unknown>;
}

const EMPTY_PROVIDER_STATE: ProviderState = {
  endpoint: "http://localhost:11434/v1",
  model: "",
  headers: {},
  bodyFields: {},
  apiKeySet: false,
  apiKeyHint: "",
};

export async function fetchProvider(): Promise<ProviderState> {
  const response = await fetch("/api/provider", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    return { ...EMPTY_PROVIDER_STATE };
  }
  return (await response.json()) as ProviderState;
}

/**
 * Write the provider configuration.
 *
 * Partial is honest rather than convenient: every field has a server-side
 * default, so an absent one means "leave it at the default" instead of "set it
 * to nothing". The settings form always sends all of them; the import path
 * sends only what the file carried.
 */
export async function setProvider(
  config: Partial<ProviderConfig>,
): Promise<ProviderState> {
  const response = await fetch("/api/provider", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!response.ok) throw new Error("Failed to save provider settings.");
  return (await response.json()) as ProviderState;
}

export async function setProviderKey(apiKey: string): Promise<ProviderState> {
  const response = await fetch("/api/provider/key", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ apiKey }),
  });
  if (!response.ok) throw new Error("Failed to save the API key.");
  return (await response.json()) as ProviderState;
}

export async function clearProviderKey(): Promise<ProviderState> {
  const response = await fetch("/api/provider/key", { method: "DELETE" });
  if (!response.ok) throw new Error("Failed to clear the API key.");
  return (await response.json()) as ProviderState;
}

export interface ProviderTestResult {
  ok: boolean;
  /** Resolved request URL, so the endpoint configuration can be checked. */
  url: string;
  /**
   * The body that was sent, so configured fields can be seen taking effect.
   *
   * Headers are absent by design: they carry the Authorization value, and a
   * diagnostic is not a reason to copy a credential into the interface.
   */
  request: Record<string, unknown>;
  /** HTTP status, or null when the request never completed. */
  status: number | null;
  response: string;
  elapsedMs: number;
  /** Empty when the request succeeded. */
  error: string;
  /** Token accounting, when the provider reports any. */
  usage: Record<string, unknown> | null;
}

/**
 * Check a configuration without saving it.
 *
 * The configuration is sent rather than the stored one, so a connection can be
 * proven before it replaces something that works. The caller supplies the
 * signal so a slow provider can be abandoned instead of holding the interface.
 */
export async function testProvider(
  config: ProviderConfig & { apiKey: string },
  signal?: AbortSignal,
): Promise<ProviderTestResult> {
  const response = await fetch("/api/provider/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
    signal,
  });
  if (!response.ok) {
    // A rejected configuration comes back as 422 with a reason; the caller
    // shows that text, so it is worth surfacing rather than flattening.
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return (await response.json()) as ProviderTestResult;
}
