import React from 'react';
import { Card } from '../shared/Card';

interface GenerationProgressProps {
  status: string;
  progress: number;
  error?: string | null;
}

export const GenerationProgress: React.FC<GenerationProgressProps> = ({
  status,
  progress,
  error
}) => {
  const getStatusInfo = (status: string) => {
    const statusMap: Record<string, { label: string; description: string }> = {
      pending: {
        label: 'Queued',
        description: 'Your generation is queued and will start soon...'
      },
      analyzing: {
        label: 'Analyzing',
        description: 'Understanding your product and audience...'
      },
      generating_copy: {
        label: 'Writing Copy',
        description: 'Crafting compelling landing page copy...'
      },
      generating_images: {
        label: 'Creating Images',
        description: 'Generating unique visuals for your page...'
      },
      assembling: {
        label: 'Assembling Page',
        description: 'Putting everything together...'
      },
      complete: {
        label: 'Complete',
        description: 'Your landing page is ready!'
      },
      failed: {
        label: 'Failed',
        description: 'Something went wrong. Please try again.'
      }
    };

    return statusMap[status] || statusMap.pending;
  };

  const statusInfo = getStatusInfo(status);
  const isComplete = status === 'complete';
  const isFailed = status === 'failed';

  return (
    <Card>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            {statusInfo.label}
          </h3>
          <span className="text-sm font-medium text-gray-600">
            {progress}%
          </span>
        </div>

        {/* Progress Bar */}
        <div className="relative pt-1">
          <div className="overflow-hidden h-3 text-xs flex rounded-full bg-gray-200">
            <div
              style={{ width: `${progress}%` }}
              className={`
                shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center
                transition-all duration-500 ease-out
                ${isFailed ? 'bg-red-500' : isComplete ? 'bg-green-500' : 'bg-indigo-600'}
              `}
            />
          </div>
        </div>

        {/* Status Description */}
        <p className={`text-sm ${isFailed ? 'text-red-600' : 'text-gray-600'}`}>
          {error || statusInfo.description}
        </p>

        {/* Loading Spinner */}
        {!isComplete && !isFailed && (
          <div className="flex justify-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        )}

        {/* Success Icon */}
        {isComplete && (
          <div className="flex justify-center py-4">
            <svg
              className="h-12 w-12 text-green-500"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
        )}

        {/* Error Icon */}
        {isFailed && (
          <div className="flex justify-center py-4">
            <svg
              className="h-12 w-12 text-red-500"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </div>
        )}
      </div>
    </Card>
  );
};
