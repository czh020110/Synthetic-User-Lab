import client from './client';
import type { FrontendSettings, FrontendSettingsUpdate } from '../types/settings';

export function getFrontendSettings(): Promise<FrontendSettings> {
  return client.get('/settings/frontend');
}

export function updateFrontendSettings(data: FrontendSettingsUpdate): Promise<FrontendSettings> {
  return client.put('/settings/frontend', data);
}
