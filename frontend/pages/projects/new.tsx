import Head from 'next/head';
import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../hooks/useAuth';
import { useProjects } from '../../hooks/useProjects';
import {
  useExtract,
  useGenerateQuestions,
  useCreateGeneration,
  useGeneration,
} from '../../hooks/useGeneration';

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

  const extractMutation = useExtract();
  const questionsMutation = useGenerateQuestions();
  const createGenerationMutation = useCreateGeneration();
  const { data: generation } = useGeneration(generationId);

  const handleCreateProject = () => {
    if (!projectName) return;
    createProject(
      { name: projectName },
      {
        onSuccess: (response: any) => {
          setProjectId(response.data.id);
          setStep(2);
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
          setStep(5);
        },
      }
    );
  };

  // Redirect when generation is complete
  if (generation?.status === 'COMPLETE' && projectId) {
    router.push(`/projects/${projectId}`);
  }

  return (
    <>
      <Head>
        <title>New Project - Launch Loop</title>
      </Head>

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
                
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="My Awesome Product"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-4"
                />
                
                <button
                  onClick={handleCreateProject}
                  disabled={!projectName}
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
                      className="w-full p-6 border-2 border-gray-200 rounded-lg hover:border-blue-600 transition text-left"
                    >
                      <h3 className="font-bold text-lg capitalize">
                        {templateId.replace('-', ' ')}
                      </h3>
                      <p className="text-gray-600 text-sm mt-1">
                        Best for early-stage products
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
                  disabled={createGenerationMutation.isPending}
                  className="w-full mt-6 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
                >
                  {createGenerationMutation.isPending ? 'Starting...' : 'Generate Landing Page'}
                </button>
              </div>
            )}

            {/* Step 5: Generating */}
            {step === 5 && generation && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mb-6"></div>
                <h2 className="text-2xl font-bold mb-4">
                  {generation.status === 'ANALYZING' && 'Analyzing your product...'}
                  {generation.status === 'GENERATING_COPY' && 'Writing copy...'}
                  {generation.status === 'GENERATING_IMAGES' && 'Creating images...'}
                  {generation.status === 'ASSEMBLING' && 'Assembling page...'}
                  {generation.status === 'COMPLETE' && 'Done! Redirecting...'}
                  {generation.status === 'FAILED' && 'Generation failed'}
                </h2>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${generation.progress}%` }}
                  />
                </div>
                <p className="text-gray-600">{generation.progress}% complete</p>
                
                {generation.status === 'FAILED' && (
                  <div className="mt-4 text-red-600">
                    {generation.error_message || 'Something went wrong'}
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
