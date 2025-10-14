import { useQuery, useMutation } from '@tanstack/react-query';
import { generateAPI } from '../lib/api';

export function useGeneration(id: string | null) {
  return useQuery({
    queryKey: ['generation', id],
    queryFn: async () => {
      if (!id) return null;
      const response = await generateAPI.get(id);
      return response.data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll every 2 seconds if generation is in progress
      const data = query.state.data as any;
      if (data && data.status !== 'COMPLETE' && data.status !== 'FAILED') {
        return 2000;
      }
      return false;
    },
  });
}

export function useExtract() {
  return useMutation({
    mutationFn: (description: string) => generateAPI.extract(description),
  });
}

export function useGenerateQuestions() {
  return useMutation({
    mutationFn: (data: { template_id: string; extracted_data: any }) =>
      generateAPI.questions(data),
  });
}

export function useCreateGeneration() {
  return useMutation({
    mutationFn: (data: any) => generateAPI.create(data),
  });
}

export function useTemplates() {
  return useQuery({
    queryKey: ['templates'],
    queryFn: async () => {
      const response = await generateAPI.templates();
      return response.data;
    },
  });
}
