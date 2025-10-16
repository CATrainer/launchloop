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
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading project...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Project not found</h1>
          <Link href="/dashboard" className="text-blue-600 hover:underline">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const isPublished = project.status === 'PUBLISHED';
  const projectUrl = project.subdomain
    ? `https://${project.subdomain}.thelaunchloop.com`
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

      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b">
          <div className="container mx-auto px-4 py-4">
            <div className="flex justify-between items-center">
              <Link href="/dashboard" className="text-blue-600 hover:underline">
                ← Back to Dashboard
              </Link>
              <span className="text-gray-600">{user?.email}</span>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8 max-w-6xl">
          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h1 className="text-3xl font-bold mb-2">{project.name}</h1>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      project.status === 'PUBLISHED'
                        ? 'bg-green-100 text-green-800'
                        : project.status === 'GENERATED'
                        ? 'bg-blue-100 text-blue-800'
                        : project.status === 'GENERATING'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {project.status}
                  </span>
                  {project.template_id && (
                    <span className="text-sm text-gray-500">
                      • {project.template_id.replace('-', ' ')}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                {project.html_content && (
                  <button
                    onClick={() => setShowPreview(!showPreview)}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                  >
                    {showPreview ? '📊 Show Stats' : '👁️ Preview Page'}
                  </button>
                )}
                {isPublished && (
                  <button
                    onClick={() => unpublishMutation.mutate()}
                    disabled={unpublishMutation.isPending}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 transition"
                  >
                    {unpublishMutation.isPending ? 'Unpublishing...' : 'Unpublish'}
                  </button>
                )}
              </div>
            </div>

            {projectUrl && (
              <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Your landing page:</p>
                <a
                  href={projectUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline font-medium"
                >
                  {projectUrl}
                </a>
              </div>
            )}

            <div className="grid md:grid-cols-3 gap-6 mb-6">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Signups</p>
                <p className="text-2xl font-bold">{project.signups_count}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Template</p>
                <p className="text-lg font-semibold capitalize">
                  {project.template_id?.replace('-', ' ') || 'None'}
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Created</p>
                <p className="text-lg font-semibold">
                  {new Date(project.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

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
                    className="text-blue-600 hover:underline text-sm"
                  >
                    Open in new tab ↗
                  </a>
                </div>
                <div className="border rounded-lg overflow-hidden bg-white">
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

                {/* Signups Section */}
                {isPublished && (
                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-4">
                      <h2 className="text-xl font-bold">Signups</h2>
                      {signups && signups.length > 0 && (
                        <button
                          onClick={() => exportMutation.mutate()}
                          disabled={exportMutation.isPending}
                          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm transition"
                        >
                          {exportMutation.isPending ? 'Exporting...' : '📥 Export CSV'}
                        </button>
                      )}
                    </div>
                    {signups && signups.length > 0 ? (
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
                                <td className="px-4 py-3 text-sm">{signup.email}</td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                  {new Date(signup.created_at).toLocaleString()}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="text-center py-12 border rounded-lg bg-gray-50">
                        <p className="text-gray-600 mb-2">📭 No signups yet</p>
                        <p className="text-sm text-gray-500">
                          Share your page to start collecting emails
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          {project.html_content && !isPublished && (
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold mb-4">Publish Your Page</h2>
              <p className="text-gray-600 mb-4">
                Choose a subdomain to make your page live
              </p>
              
              <div className="flex gap-2">
                <input
                  type="text"
                  value={subdomain}
                  onChange={(e) => setSubdomain(e.target.value.toLowerCase())}
                  placeholder="my-product"
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <span className="flex items-center text-gray-600">
                  .thelaunchloop.com
                </span>
              </div>
              
              <button
                onClick={handlePublish}
                disabled={!subdomain || publishMutation.isPending}
                className="mt-4 w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
              >
                {publishMutation.isPending ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
              <p className="text-xs text-gray-500 mt-2">
                Your page will be live at {subdomain || 'your-subdomain'}.thelaunchloop.com
              </p>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
