import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/tasks';
import type { TaskCreate, TaskUpdate } from '../types/task';

export function useTasks() {
  return useQuery({
    queryKey: ['tasks'],
    queryFn: api.listTasks,
    select: (data) => data ?? [],
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TaskCreate) => api.createTask(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskUpdate }) => api.updateTask(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteTask(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });
}
