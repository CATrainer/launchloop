import Head from 'next/head';
import Link from 'next/link';
import { useAuth } from '../hooks/useAuth';
import { useProjects } from '../hooks/useProjects';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { TierLimitBanner } from '../components/shared/TierLimitBanner';
import { projectsAPI } from '../lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';

export default function Dashboard() {
  const router = useRouter();
  const { user, isLoading: authLoading, logout } = useAuth();
  const { projects, isLoading: projectsLoading } = useProjects();
  const [loadingTooLong, setLoadingTooLong] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  // Show message if loading takes too long
  useEffect(() => {
    if (projectsLoading) {
      const timer = setTimeout(() => setLoadingTooLong(true), 5000);
      return () => clearTimeout(timer);
    } else {
      setLoadingTooLong(false);
    }
  }, [projectsLoading]);

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Get tier limits
  const getTierLimits = (tier: string) => {
    const limits: Record<string, { generations: number; revisions: number }> = {
      free: { generations: 1, revisions: 10 },
      pro: { generations: 5, revisions: -1 },
      ultimate: { generations: -1, revisions: -1 },
    };
    return limits[tier.toLowerCase()] || limits.free;
  };

  const tierLimits = getTierLimits(user.tier);
  const canCreateNew = tierLimits.generations === -1 || user.generations_used_this_month < tierLimits.generations;
  const queryClient = useQueryClient();

  // Delete project mutation
  const deleteMutation = useMutation({
    mutationFn: (projectId: string) => projectsAPI.delete(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const handleDelete = (e: React.MouseEvent, projectId: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this project?')) {
      deleteMutation.mutate(projectId);
    }
  };

  const handleResume = (e: React.MouseEvent, projectId: string) => {
    e.preventDefault();
    e.stopPropagation();
    router.push(`/projects/new?resume=${projectId}`);
  };

  return (
    <>
      <Head>
        <title>Dashboard - Launch Loop</title>
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b">
          <div className="container mx-auto px-4 py-4">
            <div className="flex justify-between items-center">
              <Link href="/" className="text-2xl font-bold text-blue-600">
                Launch Loop
              </Link>
              <div className="flex items-center space-x-4">
                <span className="text-gray-600">{user.email}</span>
                <button
                  onClick={() => logout()}
                  className="text-gray-600 hover:text-gray-900"
                >
                  Log Out
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main */}
        <main className="container mx-auto px-4 py-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">My Projects</h1>
              <p className="text-gray-600 mt-1">
                <span className="inline-block bg-gray-100 px-3 py-1 rounded-full text-sm font-semibold capitalize">
                  {user.tier} Tier
                </span>
                <span className="mx-2">•</span>
                {tierLimits.generations === -1 ? (
                  <span>Unlimited generations</span>
                ) : (
                  <span>
                    {user.generations_used_this_month} / {tierLimits.generations} generations used
                  </span>
                )}
              </p>
            </div>
            {canCreateNew ? (
              <Link
                href="/projects/new"
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                + New Project
              </Link>
            ) : (
              <button
                disabled
                className="bg-gray-300 text-gray-600 px-6 py-3 rounded-lg font-semibold cursor-not-allowed"
                title="Generation limit reached"
              >
                🚫 Limit Reached
              </button>
            )}
          </div>

          {/* Tier Limit Banner */}
          <TierLimitBanner
            tier={user.tier}
            generationsUsed={user.generations_used_this_month}
            generationsLimit={tierLimits.generations}
            revisionsUsed={user.revisions_used_this_month}
            revisionsLimit={tierLimits.revisions}
            onUpgrade={() => {}} // TODO: Add upgrade flow
          />

          {projectsLoading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
              {loadingTooLong && (
                <p className="text-gray-600 text-sm mt-4">
                  This is taking longer than expected. Please wait...
                </p>
              )}
            </div>
          ) : projects && projects.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project: any) => (
                <div
                  key={project.id}
                  className="bg-white rounded-lg shadow-sm hover:shadow-md transition p-6 relative"
                >
                  <Link href={`/projects/${project.id}`} className="block">
                    <h3 className="text-xl font-bold text-gray-900 mb-2 pr-8">
                      {project.name}
                    </h3>
                  </Link>
                  
                  <div className="flex items-center space-x-2 mb-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        project.status === 'PUBLISHED'
                          ? 'bg-green-100 text-green-800'
                          : project.status === 'GENERATED'
                          ? 'bg-blue-100 text-blue-800'
                          : project.status === 'GENERATING'
                          ? 'bg-yellow-100 text-yellow-800'
                          : project.status === 'FAILED'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {project.status}
                    </span>
                    {project.subdomain && (
                      <span className="text-xs text-gray-500 truncate">
                        {project.subdomain}.thelaunchloop.com
                      </span>
                    )}
                  </div>
                  
                  <div className="text-sm text-gray-600 mb-4">
                    <p>{project.signups_count} signups</p>
                    <p className="text-xs mt-1">
                      Created {new Date(project.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  {/* Context-aware actions */}
                  <div className="flex gap-2 border-t pt-3">
                    {project.status === 'DRAFT' && (
                      <button
                        onClick={(e) => handleResume(e, project.id)}
                        className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition"
                      >
                        📝 Resume
                      </button>
                    )}
                    {(project.status === 'GENERATED' || project.status === 'PUBLISHED') && (
                      <Link
                        href={`/projects/${project.id}`}
                        className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition text-center"
                      >
                        👁️ View
                      </Link>
                    )}
                    {project.status === 'GENERATING' && (
                      <Link
                        href={`/projects/${project.id}`}
                        className="flex-1 px-3 py-2 bg-yellow-500 text-white text-sm rounded hover:bg-yellow-600 transition text-center"
                      >
                        ⏳ Check Status
                      </Link>
                    )}
                    {project.status === 'FAILED' && (
                      <Link
                        href={`/projects/${project.id}`}
                        className="flex-1 px-3 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition text-center"
                      >
                        🔄 Retry
                      </Link>
                    )}
                    <button
                      onClick={(e) => handleDelete(e, project.id)}
                      className="px-3 py-2 border border-red-300 text-red-600 text-sm rounded hover:bg-red-50 transition"
                      disabled={deleteMutation.isPending}
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🚀</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                No projects yet
              </h2>
              <p className="text-gray-600 mb-6">
                Create your first landing page to get started
              </p>
              <Link
                href="/projects/new"
                className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                Create First Project
              </Link>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
