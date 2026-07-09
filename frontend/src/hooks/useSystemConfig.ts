import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/system';
import type { GuardConfigUpdate, ModelPresetCreate, ModelPresetUpdate } from '../types/system';

export function useModelPresets() {
  return useQuery({
    queryKey: ['model-presets'],
    queryFn: api.listModelPresets,
    select: (data) => data ?? [],
  });
}

export function useCreateModelPreset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ModelPresetCreate) => api.createModelPreset(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['model-presets'] }),
  });
}

export function useUpdateModelPreset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ModelPresetUpdate }) => api.updateModelPreset(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['model-presets'] }),
  });
}

export function useDeleteModelPreset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteModelPreset(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['model-presets'] }),
  });
}

export function useSetDefaultModelPreset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.setDefaultModelPreset(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['model-presets'] }),
  });
}

export function useGuardConfig() {
  return useQuery({
    queryKey: ['guard-config'],
    queryFn: api.getGuardConfig,
  });
}

export function useUpdateGuardConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: GuardConfigUpdate) => api.updateGuardConfig(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['guard-config'] }),
  });
}
