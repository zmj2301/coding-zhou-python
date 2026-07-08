// POST /api/logout
import { jsonResponse, clearCookieResponse, getTokenFromRequest, corsOptionsResponse } from '../_utils';

export async function onRequestPost(context: any): Promise<Response> {
  const response = jsonResponse({ success: true });
  return clearCookieResponse(response, 'wg_token');
}

export async function onRequestOptions(): Promise<Response> {
  return corsOptionsResponse();
}
