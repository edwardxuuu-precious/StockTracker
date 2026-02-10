import api from './api';

export const ingestKbFile = async ({ file, sourceType, title, metadata }) => {
  const formData = new FormData();
  formData.append('file', file);
  if (sourceType) formData.append('source_type', sourceType);
  if (title) formData.append('title', title);
  if (metadata) formData.append('metadata', JSON.stringify(metadata));
  const response = await api.post('/api/v1/kb/ingest', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const ingestKbText = async ({ sourceName, sourceType, content, title, metadata }) => {
  const formData = new FormData();
  formData.append('source_name', sourceName);
  if (sourceType) formData.append('source_type', sourceType);
  formData.append('content', content);
  if (title) formData.append('title', title);
  if (metadata) formData.append('metadata', JSON.stringify(metadata));
  const response = await api.post('/api/v1/kb/ingest-text', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const searchKb = async (payload) => {
  const response = await api.post('/api/v1/kb/search', payload);
  return response.data;
};

export const listKbDocuments = async (params = {}) => {
  const response = await api.get('/api/v1/kb/documents', { params });
  return response.data;
};

export default {
  ingestKbFile,
  ingestKbText,
  searchKb,
  listKbDocuments,
};
