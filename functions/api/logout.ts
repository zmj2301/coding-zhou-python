// POST /api/logout
import { jsonResponse, clearCookieResponse, getTokenFromRequest } from '../_utils';

export async function onRequestPost(context: any): Promise<Response> {
  const response = jsonResponse({ success: true });
  return clearCookieResponse(response, 'wg_token');
}

export async function onRequestOptions(): Promise<Response> {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}
