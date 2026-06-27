import client from './client';
import type { Persona, PersonaCreate, PersonaUpdate } from '../types/persona';

export function listPersonas(): Promise<Persona[]> {
  return client.get('/personas/');
}

export function getPersona(id: string): Promise<Persona> {
  return client.get(`/personas/${id}`);
}

export function createPersona(data: PersonaCreate): Promise<Persona> {
  return client.post('/personas/', data);
}

export function updatePersona(id: string, data: PersonaUpdate): Promise<Persona> {
  return client.put(`/personas/${id}`, data);
}

export function deletePersona(id: string): Promise<{ deleted: boolean }> {
  return client.delete(`/personas/${id}`);
}
