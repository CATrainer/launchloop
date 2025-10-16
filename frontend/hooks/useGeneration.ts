import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { generateAPI } from '../lib/api';

export function useGeneration(id: string | null) {
  // Track start time for backoff strategy
  const startTimeRef = React.useRef<number | null>(null);
  
  return useQuery({
    queryKey: ['generation', id],
    queryFn: async () => {
      if (!id) return null;
      const response = await generateAPI.get(id);
      return response.data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll with adaptive backoff based on elapsed time
      const data = query.state.data as any;
      const error = query.state.error;
      
      // Stop polling on error or if no data
      if (error || !data) return false;
      
      // Stop polling when complete or failed
      if (data.status === 'COMPLETE' || data.status === 'FAILED') {
        return false;
      }
      
      // Initialize start time on first poll
      if (!startTimeRef.current) {
        startTimeRef.current = Date.now();
      }
      
      // Adaptive polling: start fast, slow down over time
      const elapsed = Date.now() - startTimeRef.current;
      
      if (elapsed < 120000) {
        // First 2 minutes: poll every 2 seconds
        return 2000;
      } else if (elapsed < 300000) {
        // 2-5 minutes: poll every 5 seconds
        return 5000;
      } else {
        // After 5 minutes: poll every 10 seconds
        return 10000;
      }
    },
    // Retry on network errors but with backoff
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
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
