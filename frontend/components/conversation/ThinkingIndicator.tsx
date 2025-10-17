import { motion } from 'framer-motion';

interface ThinkingIndicatorProps {
  status?: string;
}

export const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({
  status = 'Thinking...',
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex gap-4 items-start"
    >
      {/* AI Avatar */}
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-ai flex items-center justify-center shadow-glow-cyan animate-pulse-slow">
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
      
      {/* Thinking Bubble */}
      <div className="flex-1 max-w-[70%]">
        <div className="bg-dark-elevated/80 backdrop-blur-md px-6 py-4 rounded-2xl rounded-tl-none border border-glass-border shadow-glass">
          <div className="flex items-center gap-3">
            {/* Animated Dots */}
            <div className="flex gap-1.5">
              {[0, 1, 2].map((index) => (
                <motion.div
                  key={index}
                  animate={{
                    scale: [1, 1.5, 1],
                    opacity: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: index * 0.2,
                    ease: 'easeInOut',
                  }}
                  className="w-2 h-2 rounded-full bg-neon-cyan"
                />
              ))}
            </div>
            
            {/* Status Text */}
            <span className="text-sm text-gray-300">
              {status}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
