const BASE_URL = '/api/v1';

async function request(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.error || 'API Request failed');
  }
  return data;
}

export const api = {
  // Chat
  sendMessage: (payload) =>
    request('/chat/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getConversations: () => request('/chat/conversations'),
  getMessages: (conversationId) =>
    request(`/chat/conversations/${conversationId}/messages`),
  deleteConversation: (conversationId) =>
    request(`/chat/conversations/${conversationId}`, { method: 'DELETE' }),
  sendFeedback: (feedback) =>
    request('/chat/feedback', {
      method: 'POST',
      body: JSON.stringify(feedback),
    }),

  // Policies
  getPolicies: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/policies/${query ? `?${query}` : ''}`);
  },
  getPolicyDetail: (id) => request(`/policies/${id}`),
  getPolicyVersions: (id) => request(`/policies/${id}/versions`),
  deletePolicy: (id) => request(`/policies/${id}`, { method: 'DELETE' }),

  // Admin Operations
  uploadPolicy: (formData) =>
    request('/admin/policies/upload', {
      method: 'POST',
      body: formData,
    }),
  getAnalytics: () => request('/admin/analytics'),
  runEvaluation: () => request('/admin/evaluate', { method: 'POST' }),
  rebuildIndex: () => request('/admin/rebuild-index', { method: 'POST' }),

  // Health
  getHealth: () => request('/health/'),
};
