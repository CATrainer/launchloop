import { motion } from 'framer-motion';
import { useEffect, useRef } from 'react';

interface ChatMessageProps {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  timestamp: Date;
  streaming?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  id,
  sender,
  content,
  timestamp,
  streaming = false,
}) => {
  const messageRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to new messages
  useEffect(() => {
    if (messageRef.current) {
      messageRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [content]);
  
  const isUser = sender === 'user';
  
  return (
    <motion.div
      ref={messageRef}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        ease: [0.23, 1, 0.32, 1], // Custom easing for smooth feel
      }}
      className={`flex gap-4 w-full ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {/* AI Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-ai flex items-center justify-center shadow-glow-cyan">
          <svg 
            className="w-6 h-6 text-white" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        </div>
      )}
      
      {/* Message Content */}
      <div className={`max-w-[70%] ${isUser ? 'order-first' : ''}`}>
        <div
          className={`
            px-6 py-4 rounded-2xl
            ${isUser 
              ? 'bg-gradient-user text-white rounded-tr-none shadow-glow-purple' 
              : 'bg-dark-elevated/80 backdrop-blur-md text-gray-100 rounded-tl-none border border-glass-border shadow-glass'
            }
          `}
        >
          {/* Markdown-style content rendering */}
          <div className="prose prose-invert max-w-none">
            {content.split('\n\n').map((paragraph, idx) => {
              // Handle bold text
              const formattedParagraph = paragraph.split('**').map((part, i) => 
                i % 2 === 0 ? part : <strong key={i} className="font-semibold text-white">{part}</strong>
              );
              
              return (
                <p key={idx} className="mb-2 last:mb-0 leading-relaxed">
                  {formattedParagraph}
                </p>
              );
            })}
          </div>
          
          {/* Streaming cursor */}
          {streaming && (
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.8, repeat: Infinity }}
              className="inline-block w-2 h-5 ml-1 bg-neon-cyan rounded-sm"
            />
          )}
        </div>
        
        {/* Timestamp */}
        <div className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
      
      {/* User Avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-user flex items-center justify-center shadow-glow-purple">
          <svg 
            className="w-6 h-6 text-white" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
        </div>
      )}
    </motion.div>
  );
};
