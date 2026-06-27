import client from './client';
import type { KnowledgeItem, KnowledgeItemCreate, KnowledgeItemUpdate, RetrievalSourceType } from '../types/knowledge';

export function listKnowledgeItems(sourceType?: RetrievalSourceType): Promise<KnowledgeItem[]> {
  const params = sourceType ? { source_type: sourceType } : undefined;
  return client.get('/knowledge/', { params });
}

export function getKnowledgeItem(id: string): Promise<KnowledgeItem> {
  return client.get(`/knowledge/${id}`);
}

export function createKnowledgeItem(data: KnowledgeItemCreate): Promise<KnowledgeItem> {
  return client.post('/knowledge/', data);
}

export function updateKnowledgeItem(id: string, data: KnowledgeItemUpdate): Promise<KnowledgeItem> {
  return client.put(`/knowledge/${id}`, data);
}

export function deleteKnowledgeItem(id: string): Promise<{ deleted: boolean }> {
  return client.delete(`/knowledge/${id}`);
}
