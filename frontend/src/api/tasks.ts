import client from './client';
import type { Task, TaskCreate, TaskUpdate } from '../types/task';

export function listTasks(): Promise<Task[]> {
  return client.get('/tasks/');
}

export function getTask(id: string): Promise<Task> {
  return client.get(`/tasks/${id}`);
}

export function createTask(data: TaskCreate): Promise<Task> {
  return client.post('/tasks/', data);
}

export function updateTask(id: string, data: TaskUpdate): Promise<Task> {
  return client.put(`/tasks/${id}`, data);
}

export function deleteTask(id: string): Promise<{ deleted: boolean }> {
  return client.delete(`/tasks/${id}`);
}
