import Head from 'next/head';
import Link from 'next/link';
import { useAuth } from '../hooks/useAuth';
import { useProjects } from '../hooks/useProjects';
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { TierLimitBanner } from '../components/shared/TierLimitBanner';

export default function Dashboard() {
  const router = useRouter();
  const { user, isLoading: authLoading, logout } = useAuth();
  const { projects, isLoading: projectsLoading } = useProjects();

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

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
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : projects && projects.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project: any) => (
                <Link
                  key={project.id}
                  href={`/projects/${project.id}`}
                  className="bg-white rounded-lg shadow-sm hover:shadow-md transition p-6"
                >
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    {project.name}
                  </h3>
                  <div className="flex items-center space-x-2 mb-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        project.status === 'PUBLISHED'
                          ? 'bg-green-100 text-green-800'
                          : project.status === 'GENERATED'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {project.status}
                    </span>
                    {project.subdomain && (
                      <span className="text-xs text-gray-500">
                        {project.subdomain}.thelaunchloop.com
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600">
                    <p>{project.signups_count} signups</p>
                    <p className="text-xs mt-1">
                      Created {new Date(project.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </Link>
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
