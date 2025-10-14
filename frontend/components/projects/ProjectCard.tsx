import React from 'react';
import { useRouter } from 'next/router';
import { Card } from '../shared/Card';
import { Button } from '../shared/Button';

interface ProjectCardProps {
  project: {
    id: string;
    name: string;
    status: string;
    subdomain?: string | null;
    signups_count: number;
    created_at: string;
    published_at?: string | null;
  };
  onDelete?: (id: string) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ project, onDelete }) => {
  const router = useRouter();

  const getStatusBadge = (status: string) => {
    const statusColors: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-800',
      generated: 'bg-blue-100 text-blue-800',
      published: 'bg-green-100 text-green-800',
      archived: 'bg-red-100 text-red-800'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status] || statusColors.draft}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{project.name}</h3>
          {getStatusBadge(project.status)}
        </div>
      </div>

      <div className="space-y-2 text-sm text-gray-600 mb-4">
        {project.subdomain && (
          <div>
            <span className="font-medium">URL:</span>{' '}
            <a
              href={`https://${project.subdomain}.thelaunchloop.com`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:underline"
            >
              {project.subdomain}.thelaunchloop.com
            </a>
          </div>
        )}
        <div>
          <span className="font-medium">Signups:</span> {project.signups_count}
        </div>
        <div>
          <span className="font-medium">Created:</span> {formatDate(project.created_at)}
        </div>
        {project.published_at && (
          <div>
            <span className="font-medium">Published:</span> {formatDate(project.published_at)}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={() => router.push(`/projects/${project.id}`)}
        >
          View
        </Button>
        {project.status === 'published' && (
          <Button
            size="sm"
            variant="secondary"
            onClick={() => window.open(`https://${project.subdomain}.thelaunchloop.com`, '_blank')}
          >
            Open Page
          </Button>
        )}
        {onDelete && (
          <Button
            size="sm"
            variant="danger"
            onClick={() => {
              if (confirm('Are you sure you want to delete this project?')) {
                onDelete(project.id);
              }
            }}
          >
            Delete
          </Button>
        )}
      </div>
    </Card>
  );
};
