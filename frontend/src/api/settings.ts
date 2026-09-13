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
  /** Whether a key is stored. The key itself is never sent to the client. */
  apiKeySet: boolean;
  /** Irreversible fragment for display only; must never be sent back. */
  apiKeyHint: string;
}

export interface ProviderConfig {
  endpoint: string;
  model: string;
  headers: Record<string, string>;
}

const EMPTY_PROVIDER_STATE: ProviderState = {
  endpoint: "http://localhost:11434",
  model: "",
  headers: {},
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

export async function setProvider(
  config: ProviderConfig,
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

export interface TestResult {
  ok: boolean;
  message: string;
}

export async function testProvider(): Promise<TestResult> {
  const response = await fetch("/api/provider/test", {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    return { ok: false, message: "Request failed" };
  }
  return (await response.json()) as TestResult;
}
