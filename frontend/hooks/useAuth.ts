import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authAPI } from '../lib/api';
import { useRouter } from 'next/router';

export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      try {
        const response = await authAPI.getMe();
        return response.data;
      } catch (error: any) {
        if (error.response?.status === 401) {
          return null;
        }
        throw error;
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const signupMutation = useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      authAPI.signup(data),
    onSuccess: (response) => {
      queryClient.setQueryData(['auth', 'me'], response.data);
      router.push('/dashboard');
    },
  });

  const loginMutation = useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      authAPI.login(data),
    onSuccess: (response) => {
      queryClient.setQueryData(['auth', 'me'], response.data);
      router.push('/dashboard');
    },
  });

  const logoutMutation = useMutation({
    mutationFn: () => authAPI.logout(),
    onSuccess: () => {
      queryClient.setQueryData(['auth', 'me'], null);
      router.push('/login');
    },
  });

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    signup: signupMutation.mutate,
    login: loginMutation.mutate,
    logout: logoutMutation.mutate,
    signupError: signupMutation.error,
    loginError: loginMutation.error,
  };
}
