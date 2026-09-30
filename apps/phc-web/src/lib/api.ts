export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8030";

/** Exactly two roles (PRD). Demo auth sends the role as a header; production uses Firebase Auth claims. */
export type Role = "phc_staff" | "district_health_officer";
let currentRole: Role = "phc_staff";
export function setRole(role: Role) {
  currentRole = role;
}

async function handle<T>(res: Response, label: string): Promise<T> {
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json()).detail ?? "";
    } catch {
      /* not JSON */
    }
    throw new Error(`${label} failed: ${res.status}${detail ? ` · ${detail}` : ""}`);
  }
  return res.json() as Promise<T>;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { headers: { "X-Role": currentRole }, cache: "no-store" });
  return handle<T>(res, `GET ${path}`);
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Role": currentRole },
    body: JSON.stringify(body ?? {}),
  });
  return handle<T>(res, `POST ${path}`);
}

export async function apiPostForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { method: "POST", headers: { "X-Role": currentRole }, body: form });
  return handle<T>(res, `POST ${path}`);
}
