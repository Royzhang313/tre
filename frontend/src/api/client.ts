const BASE = "/api/v1"

// ============================================================
// 通用请求 helper
// ============================================================

function authHeaders(): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" }
  const token = localStorage.getItem("auth_token")
  if (token) h["Authorization"] = `Bearer ${token}`
  return h
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body?.message) msg = body.message
      if (body?.detail) msg = body.detail
    } catch { /* ignore parse error */ }
    throw new Error(msg)
  }
  const json = await res.json()
  return json.data ?? json
}

// ============================================================
// HTTP Methods
// ============================================================

export async function apiGet<T = unknown>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: authHeaders() })
  return handleResponse<T>(res)
}

export async function apiPost<T = unknown>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  })
  return handleResponse<T>(res)
}

export async function apiPut<T = unknown>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: authHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  })
  return handleResponse<T>(res)
}

export async function apiPatch<T = unknown>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "PATCH",
    headers: authHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  })
  return handleResponse<T>(res)
}

export async function apiDelete<T = unknown>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "DELETE",
    headers: authHeaders(),
  })
  return handleResponse<T>(res)
}
