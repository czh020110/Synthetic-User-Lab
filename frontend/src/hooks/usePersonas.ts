import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/personas';
import type { PersonaCreate, PersonaUpdate } from '../types/persona';

export function usePersonas() {
  return useQuery({
    queryKey: ['personas'],
    queryFn: api.listPersonas,
    select: (data) => data ?? [],
  });
}

export function useCreatePersona() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PersonaCreate) => api.createPersona(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['personas'] }),
  });
}

export function useUpdatePersona() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PersonaUpdate }) => api.updatePersona(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['personas'] }),
  });
}

export function useDeletePersona() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deletePersona(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['personas'] }),
  });
}
