const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const request = async (method, path, { body, sessionId, signal } = {}) => {
  const headers = { 'Content-Type': 'application/json' };
  if (sessionId) headers['X-Session-ID'] = sessionId;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });

  return response;
};

const api = {
  getSession: (sessionId) =>
    request('GET', `/api/v1/sessions/${sessionId}`),




sendQuery: async (question, sessionId, signal) => {
  try {
    const response = await request(
      'POST',
      'http://localhost:8000/api/v1/query',
      {
        body: { question },                    // FastAPI ignores sessionId — just drop it
        headers: sessionId
          ? { 'X-Session-Id': sessionId }      // optional: pass via header for logging
          : {},
        signal,
      }
    );
    return response;
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Request cancelled');
    } else {
      console.error('Error sending query:', error);
    }
    throw error;
  }
},



  submitFeedback: (payload, sessionId) =>
    request('POST', '/api/v1/feedback', { body: payload, sessionId }),

  deleteSession: (sessionId) =>
    request('DELETE', `/api/v1/sessions/${sessionId}`),
};

export const getViewUrl = (s3Key, params) =>
  `${API_BASE_URL}/api/v1/view/${encodeURIComponent(s3Key)}?${params.toString()}`;

export default api;