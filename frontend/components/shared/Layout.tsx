import React from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../hooks/useAuth';

interface LayoutProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

export const Layout: React.FC<LayoutProps> = ({ children, requireAuth = false }) => {
  const router = useRouter();
  const { data: user, isLoading } = useAuth();

  React.useEffect(() => {
    if (requireAuth && !isLoading && !user) {
      router.push('/login');
    }
  }, [requireAuth, isLoading, user, router]);

  if (requireAuth && isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (requireAuth && !user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {user && <Navigation user={user} />}
      <main>{children}</main>
    </div>
  );
};

interface NavigationProps {
  user: any;
}

const Navigation: React.FC<NavigationProps> = ({ user }) => {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <span className="text-xl font-bold text-indigo-600">Launch Loop</span>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <a
                href="/dashboard"
                className={`${
                  router.pathname === '/dashboard'
                    ? 'border-indigo-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
              >
                Dashboard
              </a>
              <a
                href="/projects/new"
                className={`${
                  router.pathname === '/projects/new'
                    ? 'border-indigo-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
              >
                New Project
              </a>
            </div>
          </div>
          <div className="flex items-center">
            <span className="text-sm text-gray-700 mr-4">{user.email}</span>
            <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded-full mr-4">
              {user.tier.toUpperCase()}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-700 hover:text-gray-900"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};
