// GET /api/auth-check
import { checkAuth, jsonResponse, corsOptionsResponse } from '../_utils';

export async function onRequestGet(context: any): Promise<Response> {
  const { request, env } = context;
  const authenticated = await checkAuth(request, env);
  return jsonResponse({
    authenticated,
    passwordSet: Boolean(env.USER_PASSWORD)
  });
}

export async function onRequestOptions(): Promise<Response> {
  return corsOptionsResponse();
}
