import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useProject } from '@/hooks/useProjects';
import { useAuth } from '@/hooks/useAuth';
import { useState } from 'react';

export default function ProjectDetail() {
  const router = useRouter();
  const { id } = router.query;
  const { user } = useAuth();
  const { data: project, isLoading } = useProject(id as string);
  const [subdomain, setSubdomain] = useState('');

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  if (!project) {
    return <div className="min-h-screen flex items-center justify-center">Project not found</div>;
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
                <span
                  className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    isPublished
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {project.status}
                </span>
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

            {project.html_content && (
              <div className="border-t pt-6">
                <h2 className="text-xl font-bold mb-4">Preview</h2>
                <div className="border rounded-lg overflow-hidden">
                  <iframe
                    srcDoc={project.html_content}
                    className="w-full h-96"
                    title="Page Preview"
                  />
                </div>
              </div>
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
                disabled={!subdomain}
                className="mt-4 w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
              >
                Publish
              </button>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
