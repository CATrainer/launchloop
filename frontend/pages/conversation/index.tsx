import Head from 'next/head';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../hooks/useAuth';
import { useConversationStore } from '../../store/conversationStore';
import { ChatMessage } from '../../components/conversation/ChatMessage';
import { QuickReplies } from '../../components/conversation/QuickReplies';
import { TemplateCard } from '../../components/conversation/TemplateCard';
import { ThinkingIndicator } from '../../components/conversation/ThinkingIndicator';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../../lib/api';

export default function ConversationPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  
  const {
    conversationId,
    messages,
    isAIResponding,
    streamingMessageId,
    setConversationId,
    addUserMessage,
    startAIResponse,
    updateStreamedText,
    completeAIMessage,
    stopAIResponse,
  } = useConversationStore();
  
  const [userInput, setUserInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  
  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);
  
  // Initialize conversation on mount
  useEffect(() => {
    if (user && !conversationId) {
      initializeConversation();
    }
  }, [user, conversationId]);
  
  // Cleanup event source on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);
  
  const initializeConversation = async () => {
    try {
      const response = await api.post('/conversations', {});
      const conversation = response.data;
      setConversationId(conversation.id);
      
      // Load initial messages
      const messagesResponse = await api.get(`/conversations/${conversation.id}/messages`);
      const initialMessages = messagesResponse.data;
      
      // Add messages to store (skip for now, welcome message will come from backend)
    } catch (error) {
      console.error('Failed to initialize conversation:', error);
    }
  };
  
  const handleSendMessage = async () => {
    if (!userInput.trim() || !conversationId || isSending || isAIResponding) return;
    
    const message = userInput.trim();
    setUserInput('');
    setIsSending(true);
    
    // Add user message to UI immediately
    addUserMessage(message);
    
    try {
      // Send message to backend
      await api.post(`/conversations/${conversationId}/messages`, {
        message,
      });
      
      // Start streaming AI response
      streamAIResponse();
    } catch (error) {
      console.error('Failed to send message:', error);
      stopAIResponse();
    } finally {
      setIsSending(false);
    }
  };
  
  const streamAIResponse = () => {
    if (!conversationId) return;
    
    // Start AI response in UI
    const messageId = startAIResponse();
    
    // Close existing event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    
    // Create new event source for streaming
    const eventSource = new EventSource(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/conversations/${conversationId}/stream`,
      { withCredentials: true }
    );
    
    eventSourceRef.current = eventSource;
    
    let accumulatedText = '';
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'chunk') {
          // Update streamed text
          accumulatedText = data.accumulated;
          updateStreamedText(data.message_id, accumulatedText);
        } else if (data.type === 'complete') {
          // Complete message
          completeAIMessage(
            data.message_id,
            data.message_type,
            {
              quick_replies: data.quick_replies,
              templates: data.templates,
            }
          );
          
          // Close event source
          eventSource.close();
          eventSourceRef.current = null;
        } else if (data.type === 'error') {
          console.error('Stream error:', data.error);
          stopAIResponse();
          eventSource.close();
          eventSourceRef.current = null;
        }
      } catch (error) {
        console.error('Failed to parse SSE data:', error);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      stopAIResponse();
      eventSource.close();
      eventSourceRef.current = null;
    };
  };
  
  const handleQuickReply = (option: string) => {
    setUserInput(option);
    // Automatically send
    setTimeout(() => {
      handleSendMessage();
    }, 100);
  };
  
  const handleTemplateSelect = async (templateId: string) => {
    if (!conversationId) return;
    
    try {
      await api.post(`/conversations/${conversationId}/select-template`, null, {
        params: { template_id: templateId },
      });
      
      // Send confirmation message
      setUserInput(`I'd like to use the ${templateId} template`);
      setTimeout(() => {
        handleSendMessage();
      }, 100);
    } catch (error) {
      console.error('Failed to select template:', error);
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-dark-navy flex items-center justify-center">
        <div className="text-neon-cyan">Loading...</div>
      </div>
    );
  }
  
  return (
    <>
      <Head>
        <title>Create Landing Page - Launch Loop</title>
      </Head>
      
      {/* Main Container with Animated Gradient Background */}
      <div className="min-h-screen bg-dark-navy relative overflow-hidden">
        {/* Animated Background Gradient */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            background: 'linear-gradient(135deg, #0A0E27 0%, #1A2038 50%, #0A0E27 100%)',
            backgroundSize: '200% 200%',
            animation: 'gradientShift 8s ease infinite',
          }}
        />
        
        {/* Content */}
        <div className="relative z-10 max-w-5xl mx-auto px-4 py-8 h-screen flex flex-col">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between mb-6"
          >
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <span className="text-neon-cyan">✨</span> Launch Loop
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                Creating your landing page
              </p>
            </div>
            
            {/* Subtle progress dots (could expand this) */}
            <div className="flex gap-2">
              {[0, 1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full bg-glass-border"
                />
              ))}
            </div>
          </motion.div>
          
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto mb-6 space-y-6 pr-2 scrollbar-thin scrollbar-thumb-dark-elevated scrollbar-track-transparent">
            <AnimatePresence mode="popLayout">
              {messages.map((message) => (
                <div key={message.id}>
                  <ChatMessage
                    id={message.id}
                    sender={message.sender}
                    content={message.content}
                    timestamp={message.timestamp}
                    streaming={message.id === streamingMessageId}
                  />
                  
                  {/* Quick Replies */}
                  {message.messageType === 'quick_replies' && message.quickReplies && (
                    <div className="ml-14 mt-4">
                      <QuickReplies
                        options={message.quickReplies}
                        onSelect={handleQuickReply}
                      />
                    </div>
                  )}
                  
                  {/* Template Cards */}
                  {message.messageType === 'template_selection' && message.templates && (
                    <div className="mt-4">
                      {message.templates.map((template: any) => (
                        <TemplateCard
                          key={template.template.id}
                          template={template.template}
                          reasoning={template.reasoning}
                          onSelect={() => handleTemplateSelect(template.template.id)}
                        />
                      ))}
                    </div>
                  )}
                </div>
              ))}
              
              {/* Thinking Indicator */}
              {isAIResponding && !streamingMessageId && (
                <ThinkingIndicator />
              )}
            </AnimatePresence>
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input Area */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="relative"
          >
            <div className="bg-dark-elevated/80 backdrop-blur-xl rounded-2xl border border-glass-border shadow-glass p-4">
              <div className="flex gap-3 items-end">
                <textarea
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Type your message... (Shift + Enter for new line)"
                  rows={1}
                  disabled={isSending || isAIResponding}
                  className="flex-1 bg-dark-surface text-white placeholder-gray-500 rounded-xl px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-neon-cyan/50 disabled:opacity-50 disabled:cursor-not-allowed max-h-32"
                  style={{ minHeight: '48px' }}
                />
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSendMessage}
                  disabled={!userInput.trim() || isSending || isAIResponding}
                  className="bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy font-bold px-6 py-3 rounded-xl shadow-glow-cyan hover:shadow-glow-cyan disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                >
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                </motion.button>
              </div>
              
              <div className="flex items-center justify-between mt-2 px-2">
                <p className="text-xs text-gray-500">
                  Press Enter to send • Shift + Enter for new line
                </p>
                {isAIResponding && (
                  <p className="text-xs text-neon-cyan animate-pulse">
                    AI is responding...
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </>
  );
}
