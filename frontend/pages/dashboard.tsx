import Head from 'next/head';
import Link from 'next/link';
import { useAuth } from '../hooks/useAuth';
import { useProjects } from '../hooks/useProjects';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { TierLimitBanner } from '../components/shared/TierLimitBanner';
import { projectsAPI } from '../lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';

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
      <div className="min-h-screen bg-dark-navy flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-neon-cyan mb-4"></div>
          <p className="text-gray-400">Loading...</p>
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
    router.push(`/conversation?resume=${projectId}`);
  };

  return (
    <>
      <Head>
        <title>Dashboard - Launch Loop</title>
      </Head>

      <div className="min-h-screen bg-dark-navy relative overflow-hidden">
        {/* Animated Background */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background: 'linear-gradient(135deg, #0A0E27 0%, #1A2038 50%, #0A0E27 100%)',
            backgroundSize: '200% 200%',
            animation: 'gradientShift 8s ease infinite',
          }}
        />

        {/* Content */}
        <div className="relative z-10">
          {/* Header */}
          <header className="border-b border-glass-border bg-dark-elevated/60 backdrop-blur-xl">
            <div className="container mx-auto px-4 py-4">
              <div className="flex justify-between items-center">
                <Link href="/" className="text-2xl font-bold text-white flex items-center gap-2">
                  <span className="text-neon-cyan">✨</span> Launch Loop
                </Link>
                <div className="flex items-center space-x-4">
                  <span className="text-gray-400">{user.email}</span>
                  <button
                    onClick={() => logout()}
                    className="text-gray-400 hover:text-neon-cyan transition"
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
                <h1 className="text-3xl font-bold text-white">My Projects</h1>
                <p className="text-gray-400 mt-1">
                  <span className="inline-block bg-dark-elevated px-3 py-1 rounded-full text-sm font-semibold capitalize border border-neon-cyan/30">
                    {user.tier} Tier
                  </span>
                  <span className="mx-2 text-gray-600">•</span>
                  {tierLimits.generations === -1 ? (
                    <span className="text-neon-cyan">Unlimited generations</span>
                  ) : (
                    <span className="text-gray-400">
                      {user.generations_used_this_month} / {tierLimits.generations} generations used
                    </span>
                  )}
                </p>
              </div>
              {canCreateNew ? (
                <Link
                  href="/conversation"
                  className="bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy px-6 py-3 rounded-lg font-bold hover:shadow-glow-cyan transition"
                >
                  + New Project
                </Link>
              ) : (
                <button
                  disabled
                  className="bg-dark-surface text-gray-600 px-6 py-3 rounded-lg font-semibold cursor-not-allowed border border-gray-700"
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
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-neon-cyan mb-4"></div>
                {loadingTooLong && (
                  <p className="text-gray-400 text-sm mt-4">
                    This is taking longer than expected. Please wait...
                  </p>
                )}
              </div>
            ) : projects && projects.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects.map((project: any) => (
                  <motion.div
                    key={project.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    whileHover={{ scale: 1.02 }}
                    className="bg-dark-elevated/60 backdrop-blur-xl rounded-2xl border border-glass-border shadow-glass hover:border-neon-cyan/50 transition p-6 relative"
                  >
                    <Link href={`/projects/${project.id}`} className="block">
                      <h3 className="text-xl font-bold text-white mb-2 pr-8">
                        {project.name}
                      </h3>
                    </Link>
                    
                    <div className="flex items-center space-x-2 mb-3">
                      <span
                        className={`px-2 py-1 rounded text-xs font-semibold ${
                          project.status === 'PUBLISHED'
                            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                            : project.status === 'GENERATED'
                            ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                            : project.status === 'GENERATING'
                            ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                            : project.status === 'FAILED'
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                            : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
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
                    
                    <div className="text-sm text-gray-400 mb-4">
                      <p className="text-neon-cyan font-semibold">{project.signups_count} signups</p>
                      <p className="text-xs mt-1">
                        Created {new Date(project.created_at).toLocaleDateString()}
                      </p>
                    </div>

                    {/* Context-aware actions */}
                    <div className="flex gap-2 border-t border-glass-border pt-3">
                      {project.status === 'DRAFT' && (
                        <button
                          onClick={(e) => handleResume(e, project.id)}
                          className="flex-1 px-3 py-2 bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy text-sm rounded font-bold hover:shadow-glow-cyan transition"
                        >
                          📝 Resume
                        </button>
                      )}
                      {(project.status === 'GENERATED' || project.status === 'PUBLISHED') && (
                        <Link
                          href={`/projects/${project.id}`}
                          className="flex-1 px-3 py-2 bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy text-sm rounded font-bold hover:shadow-glow-cyan transition text-center"
                        >
                          👁️ View
                        </Link>
                      )}
                      {project.status === 'GENERATING' && (
                        <Link
                          href={`/projects/${project.id}`}
                          className="flex-1 px-3 py-2 bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 text-sm rounded font-bold hover:bg-yellow-500/30 transition text-center"
                        >
                          ⏳ Check Status
                        </Link>
                      )}
                      {project.status === 'FAILED' && (
                        <Link
                          href={`/projects/${project.id}`}
                          className="flex-1 px-3 py-2 bg-red-500/20 text-red-400 border border-red-500/30 text-sm rounded font-bold hover:bg-red-500/30 transition text-center"
                        >
                          🔄 Retry
                        </Link>
                      )}
                      <button
                        onClick={(e) => handleDelete(e, project.id)}
                        className="px-3 py-2 border border-red-500/30 text-red-400 text-sm rounded hover:bg-red-500/20 transition"
                        disabled={deleteMutation.isPending}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🚀</div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  No projects yet
                </h2>
                <p className="text-gray-400 mb-6">
                  Create your first landing page through natural conversation with AI
                </p>
                <Link
                  href="/conversation"
                  className="inline-block bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy px-6 py-3 rounded-lg font-bold hover:shadow-glow-cyan transition"
                >
                  Start Conversation
                </Link>
              </div>
            )}
          </main>
        </div>
      </div>
    </>
  );
}
