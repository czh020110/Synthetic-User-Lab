import client from './client';
import type {
  GuardConfig,
  GuardConfigUpdate,
  ModelPreset,
  ModelPresetCreate,
  ModelPresetUpdate,
} from '../types/system';

export function listModelPresets(): Promise<ModelPreset[]> {
  return client.get('/system/model-presets');
}

export function createModelPreset(data: ModelPresetCreate): Promise<ModelPreset> {
  return client.post('/system/model-presets', data);
}

export function setDefaultModelPreset(id: string): Promise<ModelPreset> {
  return client.put(`/system/model-presets/${id}/default`);
}

export function updateModelPreset(id: string, data: ModelPresetUpdate): Promise<ModelPreset> {
  return client.put(`/system/model-presets/${id}`, data);
}

export function deleteModelPreset(id: string): Promise<{ deleted: boolean }> {
  return client.delete(`/system/model-presets/${id}`);
}

export function getGuardConfig(): Promise<GuardConfig> {
  return client.get('/system/guard-config');
}

export function updateGuardConfig(data: GuardConfigUpdate): Promise<GuardConfig> {
  return client.put('/system/guard-config', data);
}
