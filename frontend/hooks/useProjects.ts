import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsAPI } from '../lib/api';

export function useProjects() {
  const queryClient = useQueryClient();

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await projectsAPI.list();
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string }) => projectsAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      projectsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const publishMutation = useMutation({
    mutationFn: (id: string) => projectsAPI.publish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const unpublishMutation = useMutation({
    mutationFn: (id: string) => projectsAPI.unpublish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  return {
    projects,
    isLoading,
    createProject: createMutation.mutate,
    updateProject: updateMutation.mutate,
    deleteProject: deleteMutation.mutate,
    publishProject: publishMutation.mutate,
    unpublishProject: unpublishMutation.mutate,
  };
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: async () => {
      const response = await projectsAPI.get(id);
      return response.data;
    },
    enabled: !!id,
  });
}
