import Head from 'next/head';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../hooks/useAuth';
import { useMutation } from '@tanstack/react-query';
import { projectsAPI, generateAPI } from '../../lib/api';
import { Toast } from '../../components/shared/Toast';

/**
 * Premium AI-Powered Project Creation Flow
 * 
 * Flow:
 * 1. Describe your idea (no name yet)
 * 2. AI analyzes and shows what it understood
 * 3. AI asks follow-up questions for missing context
 * 4. AI proposes name options
 * 5. Generate landing page
 */

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  data?: any;
}

export default function CreateProject() {
  const router = useRouter();
  const { user } = useAuth();
  
  // State
  const [step, setStep] = useState<'idea' | 'analysis' | 'questions' | 'name' | 'generating'>('idea');
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Data collected through the flow
  const [ideaDescription, setIdeaDescription] = useState('');
  const [extractedData, setExtractedData] = useState<any>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [nameOptions, setNameOptions] = useState<string[]>([]);
  const [selectedName, setSelectedName] = useState('');
  const [customName, setCustomName] = useState('');
  
  // Project & Generation
  const [projectId, setProjectId] = useState<string | null>(null);
  const [generationId, setGenerationId] = useState<string | null>(null);
  const [isRestoringState, setIsRestoringState] = useState(false);
  
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
  } | null>(null);

  // Mutations
  const extractMutation = useMutation({
    mutationFn: (description: string) => generateAPI.extract(description),
  });

  const questionsMutation = useMutation({
    mutationFn: (data: { template_id: string; extracted_data: any }) =>
      generateAPI.questions(data),
  });

  const createProjectMutation = useMutation({
    mutationFn: (data: { name: string }) => projectsAPI.create(data),
  });

  const createGenerationMutation = useMutation({
    mutationFn: (data: any) => generateAPI.create(data),
  });

  // Auto-save state to localStorage
  const saveStateToStorage = () => {
    if (!projectId) return;
    
    const state = {
      projectId,
      step,
      ideaDescription,
      extractedData,
      questions,
      answers,
      nameOptions,
      selectedName,
      customName,
      messages: messages.filter(m => m.role !== 'system'), // Don't save system messages
      timestamp: Date.now()
    };
    
    localStorage.setItem('launchloop_create_state', JSON.stringify(state));
  };

  // Restore state on mount
  useEffect(() => {
    const savedState = localStorage.getItem('launchloop_create_state');
    
    if (savedState) {
      try {
        const state = JSON.parse(savedState);
        
        // Check if state is recent (within 24 hours)
        const isRecent = Date.now() - state.timestamp < 24 * 60 * 60 * 1000;
        
        if (isRecent && state.projectId) {
          setIsRestoringState(true);
          
          // Restore all state
          setProjectId(state.projectId);
          setStep(state.step);
          setIdeaDescription(state.ideaDescription || '');
          setExtractedData(state.extractedData);
          setQuestions(state.questions || []);
          setAnswers(state.answers || {});
          setNameOptions(state.nameOptions || []);
          setSelectedName(state.selectedName || '');
          setCustomName(state.customName || '');
          setMessages(state.messages || []);
          
          setToast({
            message: '✨ Continuing where you left off...',
            type: 'success'
          });
          
          setTimeout(() => setIsRestoringState(false), 500);
        }
      } catch (error) {
        console.error('Failed to restore state:', error);
        localStorage.removeItem('launchloop_create_state');
      }
    }
  }, []);

  // Auto-save whenever key state changes
  useEffect(() => {
    if (projectId && !isRestoringState) {
      saveStateToStorage();
    }
  }, [step, answers, selectedName, customName, messages]);

  // Clear saved state when generation completes
  const clearSavedState = () => {
    localStorage.removeItem('launchloop_create_state');
  };

  // Step 1: Analyze idea
  const handleAnalyzeIdea = async () => {
    if (!userInput.trim()) return;
    
    setIsLoading(true);
    setIdeaDescription(userInput);
    
    // Create temporary project for state persistence (if not resuming)
    if (!projectId) {
      try {
        const tempProject = await createProjectMutation.mutateAsync({ 
          name: `Draft ${Date.now()}` 
        });
        setProjectId(tempProject.data.id);
      } catch (error) {
        console.error('Failed to create draft project:', error);
      }
    }
    
    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: userInput
    }]);
    
    try {
      const response = await extractMutation.mutateAsync(userInput);
      const extracted = response.data;
      setExtractedData(extracted);
      
      // Add AI analysis message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Great! I understand you're building ${extracted.product_type === 'b2b_saas' ? 'a B2B SaaS' : 'a product'} for ${extracted.target_audience || 'users'}.`,
        data: extracted
      }]);
      
      // Get template based on extraction
      const templateId = extracted.suggested_templates?.[0] || 'modern-saas';
      
      // Generate follow-up questions
      const questionsResponse = await questionsMutation.mutateAsync({
        template_id: templateId,
        extracted_data: extracted
      });
      
      const generatedQuestions = questionsResponse.data.questions || [];
      setQuestions(generatedQuestions);
      
      // Show what we need
      if (generatedQuestions.length > 0) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `To create an amazing landing page, I need to know a bit more. Let me ask you a few quick questions:`
        }]);
        
        // IMPORTANT: Show the FIRST question immediately
        const firstQuestion = generatedQuestions[0];
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: firstQuestion.question + (firstQuestion.example ? `\n\nExample: ${firstQuestion.example}` : '')
        }]);
        
        setStep('questions');
      } else {
        // Skip to name if we have everything
        await generateNameOptions(extracted, {});
      }
      
      setUserInput('');
    } catch (error: any) {
      setToast({
        message: error.response?.data?.detail || 'Failed to analyze your idea. Please try again.',
        type: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Handle question answers
  const handleAnswerQuestion = (questionIndex: number) => {
    if (!userInput.trim()) return;
    
    const question = questions[questionIndex];
    const newAnswers: Record<string, string> = { ...answers, [question.field]: userInput };
    setAnswers(newAnswers);
    
    // Add to messages
    setMessages(prev => [...prev, {
      role: 'user',
      content: userInput
    }]);
    
    setUserInput('');
    
    // Check if all questions answered
    const allAnswered = questions.every((q: any) => newAnswers[q.field]);
    
    if (allAnswered) {
      // Move to name selection
      generateNameOptions(extractedData, newAnswers);
    } else {
      // Show next question
      const nextUnanswered = questions.find((q: any) => !newAnswers[q.field]);
      if (nextUnanswered) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: nextUnanswered.question + (nextUnanswered.example ? `\n\nExample: ${nextUnanswered.example}` : '')
        }]);
      }
    }
  };

  // Step 3: Generate name options
  const generateNameOptions = async (extracted: any, collectedAnswers: Record<string, string>) => {
    setIsLoading(true);
    setStep('name');
    
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: '🎨 Perfect! Let me think of some great names for your product...'
    }]);
    
    try {
      // Call LLM to generate name options with proper auth
      const response = await generateAPI.names({
        extracted_data: extracted,
        answers: collectedAnswers
      });
      
      const names = response.data.names || [];
      setNameOptions(names);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `I've come up with a few name ideas based on what you've told me. Pick one or create your own:`,
        data: { names }
      }]);
    } catch (error: any) {
      // Fallback: generate simple names from extracted data
      const problem = extracted.problem || '';
      const solution = extracted.solution_approach || '';
      const words = [...problem.split(' '), ...solution.split(' ')]
        .filter(w => w.length > 3)
        .map(w => w.charAt(0).toUpperCase() + w.slice(1));
      
      const fallbackNames = [
        words.slice(0, 2).join('') || 'MyProduct',
        `${words[0] || 'Quick'}Launch`,
        `${words[0] || 'New'}Hub`,
        `${words[0] || 'Smart'}Flow`,
        `${words[0] || 'Pro'}Start`
      ];
      
      setNameOptions(fallbackNames);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Here are some name ideas. Pick one or create your own:`,
        data: { names: fallbackNames }
      }]);
      
      // Show toast that AI failed but we have fallbacks
      setToast({
        message: 'Using quick name suggestions. Feel free to enter your own!',
        type: 'info'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Step 4: Create project and generate
  const handleGenerate = async () => {
    const finalName = customName || selectedName || nameOptions[0];
    
    if (!finalName) {
      setToast({ message: 'Please select or enter a project name', type: 'error' });
      return;
    }
    
    setIsLoading(true);
    setStep('generating');
    
    try {
      // Update existing project name or create new
      if (projectId) {
        // Update draft project with final name
        await projectsAPI.update(projectId, { name: finalName });
      } else {
        // Fallback: create new project
        const projectResponse = await createProjectMutation.mutateAsync({ name: finalName });
        setProjectId(projectResponse.data.id);
      }
      
      // Start generation
      const templateId = extractedData?.suggested_templates?.[0] || 'modern-saas';
      const inputData = { ...extractedData, ...answers };
      
      const genResponse = await createGenerationMutation.mutateAsync({
        project_id: projectId!,
        template_id: templateId,
        input_data: inputData,
        type: 'NEW'
      });
      
      setGenerationId(genResponse.data.id);
      
      // Clear saved state - flow complete
      clearSavedState();
      
      // Redirect to generation status page
      router.push(`/projects/new?generation=${genResponse.data.id}`);
      
    } catch (error: any) {
      setToast({
        message: error.response?.data?.detail || 'Failed to start generation',
        type: 'error'
      });
      setIsLoading(false);
    }
  };

  // Start over - clear everything
  const handleStartOver = () => {
    if (confirm('Start over? This will clear your current progress.')) {
      clearSavedState();
      router.reload();
    }
  };

  // Get current question
  const currentQuestionIndex = questions.findIndex(q => !answers[q.field]);
  const currentQuestion = currentQuestionIndex >= 0 ? questions[currentQuestionIndex] : null;

  return (
    <>
      <Head>
        <title>Create New Project - Launch Loop</title>
      </Head>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="max-w-4xl mx-auto px-4 py-12">
          {/* Header */}
          <div className="text-center mb-12 relative">
            <h1 className="text-4xl font-bold text-gray-900 mb-3">
              ✨ Create Your Landing Page
            </h1>
            <p className="text-lg text-gray-600">
              Tell me about your idea, and I'll help you create a professional landing page
            </p>
            
            {/* Start Over button - only show if we have state */}
            {(messages.length > 0 || step !== 'idea') && (
              <button
                onClick={handleStartOver}
                className="absolute top-0 right-0 text-sm text-gray-500 hover:text-gray-700 underline"
              >
                Start Over
              </button>
            )}
          </div>

          {/* Conversation Container */}
          <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
            {/* Messages */}
            <div className="p-8 space-y-6 max-h-[600px] overflow-y-auto">
              {/* Welcome message */}
              {messages.length === 0 && step === 'idea' && (
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                      AI
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="bg-gray-50 rounded-2xl rounded-tl-none p-4 border border-gray-100">
                      <p className="text-gray-800 leading-relaxed">
                        👋 Hi! I'm your AI assistant. I'll help you create a stunning landing page in minutes.
                      </p>
                      <p className="text-gray-800 leading-relaxed mt-3">
                        <strong>Tell me about your product idea.</strong> What problem does it solve? Who is it for? What makes it special?
                      </p>
                      <p className="text-sm text-gray-500 mt-3">
                        Don't worry about being perfect - I'll ask follow-up questions if I need more details.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Conversation messages */}
              {messages.map((message, index) => (
                <div key={index} className="flex gap-4">
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                        AI
                      </div>
                    </div>
                  )}
                  
                  <div className={`flex-1 ${message.role === 'user' ? 'flex justify-end' : ''}`}>
                    <div className={`rounded-2xl p-4 max-w-[85%] ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white rounded-tr-none'
                        : 'bg-gray-50 text-gray-800 rounded-tl-none border border-gray-100'
                    }`}>
                      <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>
                      
                      {/* Show extracted data */}
                      {message.data?.problem && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <p className="text-sm text-gray-600 mb-2">Here's what I understood:</p>
                          <ul className="text-sm space-y-1">
                            <li>• <strong>Problem:</strong> {message.data.problem}</li>
                            <li>• <strong>Solution:</strong> {message.data.solution_approach}</li>
                            <li>• <strong>Audience:</strong> {message.data.target_audience}</li>
                          </ul>
                        </div>
                      )}
                      
                      {/* Show name options */}
                      {message.data?.names && (
                        <div className="mt-4 space-y-2">
                          {message.data.names.map((name: string, idx: number) => (
                            <button
                              key={idx}
                              onClick={() => setSelectedName(name)}
                              className={`block w-full text-left px-4 py-3 rounded-lg border-2 transition ${
                                selectedName === name
                                  ? 'border-blue-500 bg-blue-50'
                                  : 'border-gray-200 hover:border-blue-300'
                              }`}
                            >
                              <span className="font-semibold">{name}</span>
                            </button>
                          ))}
                          
                          <div className="pt-2">
                            <input
                              type="text"
                              value={customName}
                              onChange={(e) => {
                                setCustomName(e.target.value);
                                setSelectedName('');
                              }}
                              placeholder="Or enter your own name..."
                              className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {message.role === 'user' && (
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-700 font-bold">
                        {user?.email?.[0].toUpperCase() || 'U'}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                      AI
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="bg-gray-50 rounded-2xl rounded-tl-none p-4 border border-gray-100">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input Area */}
            {step !== 'generating' && (
              <div className="border-t border-gray-200 p-6 bg-gray-50">
                {step === 'name' && (selectedName || customName) && (
                  <button
                    onClick={handleGenerate}
                    disabled={isLoading}
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg hover:shadow-xl"
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Creating your landing page...
                      </span>
                    ) : (
                      '🚀 Create My Landing Page'
                    )}
                  </button>
                )}
                
                {step !== 'name' && (
                  <div className="flex gap-3">
                    <textarea
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          if (step === 'idea') {
                            handleAnalyzeIdea();
                          } else if (step === 'questions' && currentQuestion) {
                            handleAnswerQuestion(currentQuestionIndex);
                          }
                        }
                      }}
                      placeholder={
                        step === 'idea' 
                          ? "Describe your product idea..." 
                          : currentQuestion?.question || "Type your answer..."
                      }
                      rows={3}
                      disabled={isLoading}
                      className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition resize-none disabled:opacity-50 disabled:cursor-not-allowed"
                    />
                    <button
                      onClick={() => {
                        if (step === 'idea') {
                          handleAnalyzeIdea();
                        } else if (step === 'questions' && currentQuestion) {
                          handleAnswerQuestion(currentQuestionIndex);
                        }
                      }}
                      disabled={!userInput.trim() || isLoading}
                      className="px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition self-end"
                    >
                      Send
                    </button>
                  </div>
                )}
                
                {step === 'questions' && (
                  <p className="text-xs text-gray-500 mt-2 text-center">
                    Question {currentQuestionIndex + 1} of {questions.length} • Press Enter to send
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Progress Indicator */}
          {step !== 'generating' && (
            <div className="mt-6 flex justify-center gap-2">
              <div className={`h-2 w-16 rounded-full ${step === 'idea' ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
              <div className={`h-2 w-16 rounded-full ${step === 'questions' ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
              <div className={`h-2 w-16 rounded-full ${step === 'name' ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
