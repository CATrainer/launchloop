import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useProject } from '../../../hooks/useProjects';
import { useAuth } from '../../../hooks/useAuth';
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { projectsAPI, signupsAPI, generateAPI } from '../../../lib/api';
import { Toast } from '../../../components/shared/Toast';

export default function ProjectDetail() {
  const router = useRouter();
  const { id } = router.query;
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { data: project, isLoading } = useProject(id as string);
  const [subdomain, setSubdomain] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [showExtractedData, setShowExtractedData] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Fetch signups
  const { data: signups } = useQuery({
    queryKey: ['signups', id],
    queryFn: async () => {
      if (!id) return [];
      const response = await signupsAPI.list(id as string);
      return response.data;
    },
    enabled: !!id && project?.status === 'PUBLISHED',
  });

  // Publish mutation
  const publishMutation = useMutation({
    mutationFn: async (subdomainValue: string) => {
      // First update the project with subdomain
      await projectsAPI.update(id as string, { subdomain: subdomainValue });
      // Then publish
      return projectsAPI.publish(id as string);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      setToast({ message: 'Project published successfully!', type: 'success' });
      setSubdomain('');
    },
    onError: (error: any) => {
      setToast({
        message: error.response?.data?.detail || 'Failed to publish project',
        type: 'error',
      });
    },
  });

  // Unpublish mutation
  const unpublishMutation = useMutation({
    mutationFn: () => projectsAPI.unpublish(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      setToast({ message: 'Project unpublished successfully', type: 'success' });
    },
    onError: (error: any) => {
      setToast({
        message: error.response?.data?.detail || 'Failed to unpublish project',
        type: 'error',
      });
    },
  });

  // Retry generation mutation
  const retryMutation = useMutation({
    mutationFn: () => generateAPI.retry(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      setToast({ message: 'Generation restarted! Redirecting...', type: 'success' });
      setTimeout(() => {
        router.push(`/projects/new?resume=${id}`);
      }, 1500);
    },
    onError: (error: any) => {
      setToast({
        message: error.response?.data?.detail || 'Failed to retry generation',
        type: 'error',
      });
    },
  });

  // Export signups mutation
  const exportMutation = useMutation({
    mutationFn: () => signupsAPI.export(id as string),
    onSuccess: (response) => {
      // Create download link
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `signups_${project?.subdomain || 'export'}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setToast({ message: 'Signups exported successfully', type: 'success' });
    },
    onError: () => {
      setToast({ message: 'Failed to export signups', type: 'error' });
    },
  });

  const handlePublish = () => {
    if (!subdomain || subdomain.length < 3) {
      setToast({ message: 'Subdomain must be at least 3 characters', type: 'error' });
      return;
    }
    publishMutation.mutate(subdomain);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-navy flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-neon-cyan mb-4"></div>
          <p className="text-gray-400">Loading project...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-dark-navy flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-2">Project not found</h1>
          <Link href="/dashboard" className="text-neon-cyan hover:underline">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  // Check if published by looking at published_at, not status
  // Status can be 'GENERATED' but project can still be published
  const isPublished = !!project.published_at;
  const projectUrl = project.subdomain
    ? `https://${project.subdomain}.thelaunchloop.com`
    : project.custom_domain
    ? `https://${project.custom_domain}`
    : null;

  return (
    <>
      <Head>
        <title>{project.name} - Launch Loop</title>
      </Head>

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

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
          <header className="border-b border-glass-border bg-dark-elevated/60 backdrop-blur-xl">
            <div className="container mx-auto px-4 py-4">
              <div className="flex justify-between items-center">
                <Link href="/dashboard" className="text-neon-cyan hover:underline font-semibold">
                  ← Back to Dashboard
                </Link>
                <span className="text-gray-400">{user?.email}</span>
              </div>
            </div>
          </header>

          <main className="container mx-auto px-4 py-8 max-w-6xl">
            <div className="bg-dark-elevated/60 backdrop-blur-xl rounded-2xl border border-glass-border shadow-glass p-8 mb-8">
            <div className="flex justify-between items-start mb-6">
                <div>
                  <h1 className="text-3xl font-bold mb-2 text-white">{project.name}</h1>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-semibold border ${
                      project.status === 'PUBLISHED'
                        ? 'bg-green-500/20 text-green-400 border-green-500/30'
                        : project.status === 'GENERATED'
                        ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                        : project.status === 'GENERATING'
                        ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
                        : 'bg-gray-500/20 text-gray-400 border-gray-500/30'
                    }`}
                  >
                    {project.status}
                  </span>
                  {project.template_id && (
                    <span className="text-sm text-gray-400">
                      • {project.template_id.replace('-', ' ')}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                {project.status === 'FAILED' && (
                  <button
                    onClick={() => retryMutation.mutate()}
                    disabled={retryMutation.isPending}
                    className="px-4 py-2 bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy rounded-lg font-bold hover:shadow-glow-cyan disabled:opacity-50 transition flex items-center gap-2"
                  >
                    <span>🔄</span>
                    {retryMutation.isPending ? 'Restarting...' : 'Retry Generation'}
                  </button>
                )}
                {project.html_content && (
                  <button
                    onClick={() => setShowPreview(!showPreview)}
                    className="px-4 py-2 border border-glass-border rounded-lg hover:bg-dark-surface transition text-gray-300"
                  >
                    {showPreview ? '📊 Show Stats' : '👁️ Preview Page'}
                  </button>
                )}
                {isPublished && (
                  <button
                    onClick={() => unpublishMutation.mutate()}
                    disabled={unpublishMutation.isPending}
                    className="px-4 py-2 bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/30 disabled:opacity-50 transition font-bold"
                  >
                    {unpublishMutation.isPending ? 'Unpublishing...' : 'Unpublish'}
                  </button>
                )}
              </div>
            </div>

            {/* Failed State Alert */}
            {project.status === 'FAILED' && (
              <div className="mb-6 p-4 bg-red-500/10 border-2 border-red-500/30 rounded-lg">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">⚠️</span>
                  <div className="flex-1">
                    <h3 className="font-semibold text-red-400 mb-1">Generation Failed</h3>
                    <p className="text-sm text-red-300 mb-3">
                      Something went wrong during generation. This could be due to API rate limits or a temporary issue.
                    </p>
                    <button
                      onClick={() => retryMutation.mutate()}
                      disabled={retryMutation.isPending}
                      className="px-4 py-2 bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/30 disabled:opacity-50 transition text-sm font-bold"
                    >
                      {retryMutation.isPending ? 'Restarting...' : '🔄 Retry Generation'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Generating State Alert */}
            {project.status === 'GENERATING' && (
              <div className="mb-6 p-4 bg-yellow-500/10 border-2 border-yellow-500/30 rounded-lg">
                <div className="flex items-start gap-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-400"></div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-yellow-400 mb-1">Generation in Progress</h3>
                    <p className="text-sm text-yellow-300">
                      This typically takes 60-120 seconds. You can close this page and come back later.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {projectUrl && (
              <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <p className="text-sm text-gray-400 mb-2">Your landing page:</p>
                <a
                  href={projectUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-neon-cyan hover:underline font-medium"
                >
                  {projectUrl}
                </a>
              </div>
            )}

            <div className="grid md:grid-cols-3 gap-6 mb-6">
              <div className="p-4 bg-dark-surface border border-glass-border rounded-lg">
                <p className="text-sm text-gray-400">Signups</p>
                <p className="text-2xl font-bold text-neon-cyan">{project.signups_count}</p>
              </div>
              <div className="p-4 bg-dark-surface border border-glass-border rounded-lg">
                <p className="text-sm text-gray-400">Template</p>
                <p className="text-lg font-semibold capitalize text-white">
                  {project.template_id?.replace('-', ' ') || 'None'}
                </p>
              </div>
              <div className="p-4 bg-dark-surface border border-glass-border rounded-lg">
                <p className="text-sm text-gray-400">Created</p>
                <p className="text-lg font-semibold text-white">
                  {new Date(project.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* Extracted Data Section */}
            {project.generated_data && Object.keys(project.generated_data).length > 0 && (
              <div className="mb-6">
                <button
                  onClick={() => setShowExtractedData(!showExtractedData)}
                  className="w-full text-left p-4 bg-dark-surface border border-glass-border hover:bg-dark-elevated rounded-lg transition flex justify-between items-center"
                >
                  <span className="font-semibold text-white">📋 Extracted Product Data</span>
                  <span className="text-gray-400">{showExtractedData ? '▼' : '▶'}</span>
                </button>
                {showExtractedData && (
                  <div className="mt-2 p-4 border border-glass-border rounded-lg bg-dark-surface">
                    <div className="grid md:grid-cols-2 gap-4">
                      {Object.entries(project.generated_data).map(([key, value]) => (
                        <div key={key} className="p-3 bg-dark-elevated border border-glass-border rounded">
                          <p className="text-xs text-gray-400 mb-1 font-medium uppercase">
                            {key.replace(/_/g, ' ')}
                          </p>
                          <p className="text-sm text-white">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Preview Mode */}
            {showPreview && project.html_content && (
              <div className="border-t pt-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-bold">Preview</h2>
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      const win = window.open('', '_blank');
                      if (win) {
                        win.document.write(project.html_content);
                        win.document.close();
                      }
                    }}
                    className="text-neon-cyan hover:underline text-sm font-semibold"
                  >
                    Open in new tab ↗
                  </a>
                </div>
                <div className="border border-glass-border rounded-lg overflow-hidden bg-dark-surface">
                  <iframe
                    srcDoc={project.html_content}
                    className="w-full"
                    style={{ height: '600px' }}
                    title="Page Preview"
                    sandbox="allow-same-origin"
                  />
                </div>
              </div>
            )}

            {/* Stats Mode (default) */}
            {!showPreview && (
              <>
                {/* Published URL */}
                {projectUrl && (
                  <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600 mb-1">🌐 Live at:</p>
                        <a
                          href={projectUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-700 hover:underline font-medium text-lg"
                        >
                          {projectUrl}
                        </a>
                      </div>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(projectUrl);
                          setToast({ message: 'URL copied to clipboard', type: 'success' });
                        }}
                        className="px-3 py-2 border border-green-300 rounded-lg hover:bg-green-100 text-sm transition"
                      >
                        📋 Copy URL
                      </button>
                    </div>
                  </div>
                )}

                {/* Signups Section - Always show if page has content */}
                {project.html_content && (
                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-4">
                      <h2 className="text-xl font-bold">Email Signups</h2>
                      {isPublished && signups && signups.length > 0 && (
                        <button
                          onClick={() => exportMutation.mutate()}
                          disabled={exportMutation.isPending}
                          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm transition"
                        >
                          {exportMutation.isPending ? 'Exporting...' : '📥 Export CSV'}
                        </button>
                      )}
                    </div>
                    
                    {!isPublished ? (
                      <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
                        <p className="text-gray-600 mb-2">📧 Email collection ready</p>
                        <p className="text-sm text-gray-500 mb-3">
                          Publish your page to start collecting signups
                        </p>
                        <p className="text-xs text-gray-400">
                          Emails will appear here once your page is live
                        </p>
                      </div>
                    ) : signups && signups.length > 0 ? (
                      <div className="border rounded-lg overflow-hidden">
                        <table className="w-full">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                                Email
                              </th>
                              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                                Signed Up
                              </th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {signups.map((signup: any) => (
                              <tr key={signup.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 text-sm font-medium">{signup.email}</td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                  {new Date(signup.created_at).toLocaleString()}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="text-center py-12 border rounded-lg bg-blue-50 border-blue-200">
                        <p className="text-blue-900 mb-2 font-medium">📭 No signups yet</p>
                        <p className="text-sm text-blue-700 mb-3">
                          Your page is live at {projectUrl}
                        </p>
                        <p className="text-xs text-blue-600">
                          Share your link to start collecting emails!
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          {project.html_content && !isPublished && (
            <div className="bg-dark-elevated/60 backdrop-blur-xl rounded-2xl border border-glass-border shadow-glass p-8">
              <h2 className="text-2xl font-bold mb-4 text-white">Publish Your Page</h2>
              <p className="text-gray-400 mb-4">
                Choose a subdomain to make your page live
              </p>
              
              <div className="flex gap-2">
                <input
                  type="text"
                  value={subdomain}
                  onChange={(e) => setSubdomain(e.target.value.toLowerCase())}
                  placeholder="my-product"
                  className="flex-1 px-4 py-3 bg-dark-surface border border-glass-border rounded-lg focus:ring-2 focus:ring-neon-cyan/50 text-white placeholder-gray-500 outline-none transition"
                />
                <span className="flex items-center text-gray-400">
                  .thelaunchloop.com
                </span>
              </div>
              
              <button
                onClick={handlePublish}
                disabled={publishMutation.isPending || !subdomain}
                className="px-6 py-3 bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy rounded-lg font-bold hover:shadow-glow-cyan disabled:opacity-50 transition flex items-center gap-2"
              >
                {publishMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Publishing...
                  </span>
                ) : (
                  '🚀 Publish Page'
                )}
              </button>
              <p className="text-xs text-gray-400 mt-2">
                Your page will be live at {subdomain || 'your-subdomain'}.thelaunchloop.com
              </p>
            </div>
          )}
          </main>
        </div>
      </div>
    </>
  );
}
