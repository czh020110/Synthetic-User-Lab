import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/knowledge';
import type { KnowledgeItemCreate, KnowledgeItemUpdate, RetrievalSourceType } from '../types/knowledge';

export function useKnowledgeItems(sourceType?: RetrievalSourceType) {
  return useQuery({
    queryKey: ['knowledge', sourceType ? { source_type: sourceType } : {}],
    queryFn: () => api.listKnowledgeItems(sourceType),
    select: (data) => data ?? [],
  });
}

export function useCreateKnowledgeItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: KnowledgeItemCreate) => api.createKnowledgeItem(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['knowledge'] }),
  });
}

export function useUpdateKnowledgeItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: KnowledgeItemUpdate }) => api.updateKnowledgeItem(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['knowledge'] }),
  });
}

export function useDeleteKnowledgeItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteKnowledgeItem(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['knowledge'] }),
  });
}
