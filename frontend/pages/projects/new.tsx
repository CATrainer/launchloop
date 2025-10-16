import Head from 'next/head';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../hooks/useAuth';
import { useProjects, useProject } from '../../hooks/useProjects';
import {
  useExtract,
  useGenerateQuestions,
  useCreateGeneration,
  useGeneration,
} from '../../hooks/useGeneration';
import { Toast } from '../../components/shared/Toast';
import { TierLimitBanner } from '../../components/shared/TierLimitBanner';
import { projectsAPI } from '../../lib/api';
import { useMutation } from '@tanstack/react-query';

export default function NewProject() {
  const router = useRouter();
  const { user } = useAuth();
  const { createProject } = useProjects();
  
  const [step, setStep] = useState(1);
  const [projectName, setProjectName] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const [description, setDescription] = useState('');
  const [extractedData, setExtractedData] = useState<any>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [generationId, setGenerationId] = useState<string | null>(null);
  const [generationStartTime, setGenerationStartTime] = useState<number | null>(null);
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
  } | null>(null);

  const extractMutation = useExtract();
  const questionsMutation = useGenerateQuestions();
  const createGenerationMutation = useCreateGeneration();
  const { data: generation } = useGeneration(generationId);

  // State persistence mutation
  const saveStateMutation = useMutation({
    mutationFn: (state: any) => projectsAPI.saveState(projectId!, state),
  });

  // Load existing project if resuming
  const { data: existingProject } = useProject(router.query.resume as string);

  // Restore state from existing project
  useEffect(() => {
    if (existingProject && existingProject.creation_state) {
      const state = existingProject.creation_state;
      setProjectId(existingProject.id);
      setProjectName(existingProject.name);
      setStep(state.step || 1);
      setDescription(state.description || '');
      setExtractedData(state.extracted_data || null);
      setSelectedTemplate(state.selected_template || null);
      setQuestions(state.questions || []);
      setAnswers(state.answers || {});
      if (state.generation_id) {
        setGenerationId(state.generation_id);
      }
    }
  }, [existingProject]);

  // Save state whenever it changes (debounced)
  useEffect(() => {
    if (projectId && step > 1) {
      const timer = setTimeout(() => {
        saveStateMutation.mutate({
          step,
          description,
          extracted_data: extractedData,
          selected_template: selectedTemplate,
          questions,
          answers,
          generation_id: generationId,
        });
      }, 1000); // Debounce 1 second
      return () => clearTimeout(timer);
    }
  }, [projectId, step, description, extractedData, selectedTemplate, questions, answers, generationId]);

  const handleCreateProject = () => {
    if (!projectName || projectName.length > 255) return;
    createProject(
      { name: projectName },
      {
        onSuccess: (response: any) => {
          setProjectId(response.data.id);
          setStep(2);
        },
        onError: (error: any) => {
          const errorMessage = error.response?.data?.detail || 'Failed to create project. Please try again.';
          setToast({
            message: Array.isArray(errorMessage) 
              ? errorMessage.map((e: any) => e.msg).join(', ')
              : errorMessage,
            type: 'error',
          });
        },
      }
    );
  };

  const handleExtract = () => {
    extractMutation.mutate(description, {
      onSuccess: (response) => {
        setExtractedData(response.data);
        setStep(3);
      },
      onError: (error: any) => {
        setToast({
          message: error.response?.data?.detail || 'Failed to analyze your product description. Please try again.',
          type: 'error',
        });
      },
    });
  };

  const handleSelectTemplate = (templateId: string) => {
    setSelectedTemplate(templateId);
    
    questionsMutation.mutate(
      {
        template_id: templateId,
        extracted_data: extractedData,
      },
      {
        onSuccess: (response) => {
          setQuestions(response.data.questions);
          setStep(4);
        },
        onError: (error: any) => {
          setToast({
            message: error.response?.data?.detail || 'Failed to generate questions. Please try again.',
            type: 'error',
          });
        },
      }
    );
  };

  const handleGenerate = () => {
    if (!projectId || !selectedTemplate) return;

    const inputData = {
      ...extractedData,
      ...answers,
    };

    createGenerationMutation.mutate(
      {
        project_id: projectId,
        template_id: selectedTemplate,
        input_data: inputData,
        type: 'new',
      },
      {
        onSuccess: (response) => {
          setGenerationId(response.data.id);
          setGenerationStartTime(Date.now());
          setShowTimeoutWarning(false);
          setStep(5);
        },
        onError: (error: any) => {
          const errorDetail = error.response?.data?.detail;
          
          // Check if it's a generation limit error with detailed info
          if (error.response?.status === 403 && typeof errorDetail === 'object') {
            const { message, tier, generations_used, generations_limit, usage_reset_date } = errorDetail;
            const resetDate = usage_reset_date ? new Date(usage_reset_date).toLocaleDateString() : 'next month';
            setToast({
              message: `${message} (${generations_used}/${generations_limit} used on ${tier} tier). Resets ${resetDate}.`,
              type: 'error',
            });
          } else if (error.response?.status === 403) {
            setToast({
              message: (typeof errorDetail === 'string' ? errorDetail : errorDetail?.message) + ' You\'ve reached your monthly generation limit.',
              type: 'error',
            });
          } else {
            setToast({
              message: typeof errorDetail === 'string' ? errorDetail : 'Failed to start generation. Please try again.',
              type: 'error',
            });
          }
        },
      }
    );
  };

  // Monitor generation timeout
  useEffect(() => {
    if (generationStartTime && generation && generation.status !== 'COMPLETE' && generation.status !== 'FAILED') {
      const elapsed = Date.now() - generationStartTime;
      
      // Show warning after 3 minutes
      if (elapsed > 180000 && !showTimeoutWarning) {
        setShowTimeoutWarning(true);
      }
      
      // Show critical warning after 5 minutes
      if (elapsed > 300000) {
        setToast({
          message: 'Generation is taking longer than expected. You can check back later.',
          type: 'warning',
        });
      }
    }
  }, [generation, generationStartTime, showTimeoutWarning]);

  // Redirect when generation is complete
  useEffect(() => {
    if (generation?.status === 'COMPLETE' && projectId) {
      setTimeout(() => {
        router.push(`/projects/${projectId}`);
      }, 1000);
    }
  }, [generation?.status, projectId, router]);

  // Get tier limits
  const getTierLimits = (tier: string) => {
    const limits: Record<string, { generations: number; revisions: number }> = {
      free: { generations: 1, revisions: 10 },
      pro: { generations: 5, revisions: -1 },
      ultimate: { generations: -1, revisions: -1 },
    };
    return limits[tier.toLowerCase()] || limits.free;
  };

  const tierLimits = user ? getTierLimits(user.tier) : { generations: 0, revisions: 0 };

  return (
    <>
      <Head>
        <title>New Project - Launch Loop</title>
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
            <Link href="/dashboard" className="text-2xl font-bold text-blue-600">
              Launch Loop
            </Link>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8 max-w-3xl">
          <div className="bg-white rounded-xl shadow-lg p-8">
            {/* Step 1: Project Name */}
            {step === 1 && (
              <div>
                <h1 className="text-3xl font-bold mb-2">Create New Project</h1>
                <p className="text-gray-600 mb-6">Give your project a name</p>
                
                <div className="mb-4">
                  <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value.slice(0, 255))}
                    placeholder="My Awesome Product"
                    maxLength={255}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                      projectName.length > 255 ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  <div className="flex justify-between items-center mt-2">
                    <p className="text-xs text-gray-500">
                      {projectName.length > 200 && projectName.length <= 255 && (
                        <span className="text-yellow-600">⚠️ Getting close to limit</span>
                      )}
                      {projectName.length > 255 && (
                        <span className="text-red-600">❌ Name is too long</span>
                      )}
                    </p>
                    <p className={`text-xs ${
                      projectName.length > 240 ? 'text-red-600 font-semibold' : 
                      projectName.length > 200 ? 'text-yellow-600' : 
                      'text-gray-400'
                    }`}>
                      {projectName.length}/255
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={handleCreateProject}
                  disabled={!projectName || projectName.length > 255}
                  className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
                >
                  Continue
                </button>
              </div>
            )}

            {/* Step 2: Description */}
            {step === 2 && (
              <div>
                <h1 className="text-3xl font-bold mb-2">Describe Your Product</h1>
                <p className="text-gray-600 mb-6">
                  Tell us about your product in a few sentences or upload a document
                </p>
                
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="We're building a tool that helps solo founders..."
                  rows={8}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-4"
                />
                
                <button
                  onClick={handleExtract}
                  disabled={!description || extractMutation.isPending}
                  className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
                >
                  {extractMutation.isPending ? 'Analyzing...' : 'Continue'}
                </button>
              </div>
            )}

            {/* Step 3: Template Selection */}
            {step === 3 && extractedData && (
              <div>
                <h1 className="text-3xl font-bold mb-2">Choose Template</h1>
                <p className="text-gray-600 mb-6">
                  Based on your product, we recommend these templates
                </p>
                
                <div className="space-y-4">
                  {extractedData.suggested_templates?.map((templateId: string) => (
                    <button
                      key={templateId}
                      onClick={() => handleSelectTemplate(templateId)}
                      disabled={questionsMutation.isPending}
                      className={`w-full p-6 border-2 rounded-lg transition text-left relative ${
                        questionsMutation.isPending
                          ? 'border-blue-400 bg-blue-50 cursor-wait'
                          : 'border-gray-200 hover:border-blue-600'
                      }`}
                    >
                      {questionsMutation.isPending && (
                        <div className="absolute top-6 right-6">
                          <svg
                            className="animate-spin h-5 w-5 text-blue-600"
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
                        </div>
                      )}
                      <h3 className="font-bold text-lg capitalize">
                        {templateId.replace('-', ' ')}
                      </h3>
                      <p className="text-gray-600 text-sm mt-1">
                        {questionsMutation.isPending ? 'Loading questions...' : 'Best for early-stage products'}
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 4: Questions */}
            {step === 4 && questions.length > 0 && (
              <div>
                <h1 className="text-3xl font-bold mb-2">Fill in Details</h1>
                <p className="text-gray-600 mb-6">
                  Answer these questions to personalize your landing page
                </p>
                
                {/* Tier Limit Warning */}
                {user && (
                  <TierLimitBanner
                    tier={user.tier}
                    generationsUsed={user.generations_used_this_month}
                    generationsLimit={tierLimits.generations}
                    revisionsUsed={user.revisions_used_this_month}
                    revisionsLimit={tierLimits.revisions}
                    onUpgrade={() => router.push('/dashboard')} // TODO: Add upgrade flow
                  />
                )}
                
                <div className="space-y-6">
                  {questions.map((q: any) => (
                    <div key={q.field}>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {q.question}
                        {q.required && <span className="text-red-500"> *</span>}
                      </label>
                      {q.example && (
                        <p className="text-xs text-gray-500 mb-2">
                          Example: {q.example}
                        </p>
                      )}
                      <textarea
                        value={answers[q.field] || ''}
                        onChange={(e) =>
                          setAnswers({ ...answers, [q.field]: e.target.value })
                        }
                        rows={3}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  ))}
                </div>
                
                <button
                  onClick={handleGenerate}
                  disabled={
                    createGenerationMutation.isPending ||
                    (tierLimits.generations !== -1 &&
                      user &&
                      user.generations_used_this_month >= tierLimits.generations)
                  }
                  className="w-full mt-6 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
                >
                  {createGenerationMutation.isPending ? (
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
                      Starting generation...
                    </span>
                  ) : tierLimits.generations !== -1 &&
                    user &&
                    user.generations_used_this_month >= tierLimits.generations ? (
                    '🚫 Generation Limit Reached - Upgrade to Continue'
                  ) : (
                    '🚀 Generate Landing Page'
                  )}
                </button>
              </div>
            )}

            {/* Step 5: Loading */}
            {step === 5 && !generation && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mb-6"></div>
                <h2 className="text-2xl font-bold mb-4">Starting generation...</h2>
                <p className="text-gray-600">Setting up your landing page generation</p>
              </div>
            )}

            {/* Step 5: Generating */}
            {step === 5 && generation && (
              <div className="text-center py-12">
                {generation.status !== 'FAILED' && generation.status !== 'COMPLETE' && (
                  <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mb-6"></div>
                )}
                
                {generation.status === 'COMPLETE' && (
                  <div className="text-6xl mb-4">✅</div>
                )}
                
                {generation.status === 'FAILED' && (
                  <div className="text-6xl mb-4">❌</div>
                )}
                
                <h2 className="text-2xl font-bold mb-4">
                  {generation.status === 'ANALYZING' && 'Analyzing your product...'}
                  {generation.status === 'GENERATING_COPY' && 'Writing copy...'}
                  {generation.status === 'GENERATING_IMAGES' && 'Creating images...'}
                  {generation.status === 'ASSEMBLING' && 'Assembling page...'}
                  {generation.status === 'COMPLETE' && 'Generation Complete!'}
                  {generation.status === 'FAILED' && 'Generation Failed'}
                </h2>
                
                {generation.status !== 'FAILED' && generation.status !== 'COMPLETE' && (
                  <>
                    <div className="w-full bg-gray-200 rounded-full h-3 mb-4 max-w-md mx-auto">
                      <div
                        className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${generation.progress}%` }}
                      />
                    </div>
                    <p className="text-gray-600 mb-6">{generation.progress}% complete</p>
                    
                    <p className="text-sm text-gray-500 mb-4">
                      This usually takes 60-120 seconds
                    </p>
                    
                    {showTimeoutWarning && (
                      <div className="max-w-md mx-auto mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-sm text-yellow-800 mb-2">
                          ⏱️ Taking longer than expected...
                        </p>
                        <p className="text-xs text-yellow-700">
                          You can safely close this page and check back later. Your generation will continue in the background.
                        </p>
                      </div>
                    )}
                  </>
                )}
                
                {generation.status === 'COMPLETE' && (
                  <div className="max-w-md mx-auto">
                    <p className="text-gray-600 mb-4">Redirecting to your project...</p>
                    <div className="flex justify-center">
                      <Link
                        href={`/projects/${projectId}`}
                        className="text-blue-600 hover:underline text-sm"
                      >
                        Or click here to view now →
                      </Link>
                    </div>
                  </div>
                )}
                
                {generation.status === 'FAILED' && (
                  <div className="max-w-md mx-auto">
                    <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-red-800 mb-2">
                        {generation.error_message || 'Something went wrong during generation'}
                      </p>
                      <p className="text-sm text-red-600">
                        This could be due to API rate limits or a temporary issue.
                      </p>
                    </div>
                    <div className="flex flex-col gap-3">
                      <Link
                        href={`/projects/${projectId}`}
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
                      >
                        🔄 Go to Project & Retry
                      </Link>
                      <Link
                        href="/dashboard"
                        className="text-gray-600 hover:underline text-sm"
                      >
                        ← Back to Dashboard
                      </Link>
                    </div>
                  </div>
                )}
                
                {(generation.status === 'GENERATING_COPY' || 
                  generation.status === 'GENERATING_IMAGES' || 
                  generation.status === 'ASSEMBLING') && (
                  <div className="mt-8">
                    <Link
                      href={`/projects/${projectId}`}
                      className="text-sm text-gray-500 hover:text-gray-700 underline"
                    >
                      View project page (generation continues in background)
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
