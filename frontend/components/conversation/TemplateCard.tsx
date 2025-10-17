import { motion } from 'framer-motion';
import { useState } from 'react';
import Image from 'next/image';

interface TemplateCardProps {
  template: {
    id: string;
    name: string;
    description: string;
    preview_image: string;
  };
  reasoning: string;
  onSelect: () => void;
}

export const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  reasoning,
  onSelect,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, type: 'spring' }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className="w-full max-w-2xl mx-auto my-6"
    >
      <motion.div
        whileHover={{
          scale: 1.02,
          rotateX: 2,
          rotateY: -2,
          z: 50,
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        style={{ transformStyle: 'preserve-3d' }}
        className="relative bg-dark-elevated/60 backdrop-blur-xl rounded-2xl border border-glass-border shadow-glass overflow-hidden"
      >
        {/* Glow effect on hover */}
        {isHovered && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-gradient-to-br from-neon-cyan/10 via-transparent to-neon-purple/10 pointer-events-none"
          />
        )}
        
        {/* Preview Image */}
        <div className="relative h-64 bg-gradient-to-br from-dark-surface to-dark-elevated overflow-hidden">
          <div className="absolute inset-0 flex items-center justify-center">
            {/* Placeholder for now - will be replaced with actual preview */}
            <div className="text-6xl">🎨</div>
          </div>
          
          {/* Border gradient */}
          <div className="absolute inset-0 border-b-2 border-neon-cyan/30" />
        </div>
        
        {/* Content */}
        <div className="p-6">
          {/* Template Name & Description */}
          <h3 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
            {template.name}
            <span className="px-2 py-1 text-xs bg-neon-cyan/20 text-neon-cyan rounded-full border border-neon-cyan/30">
              Recommended
            </span>
          </h3>
          
          <p className="text-gray-400 mb-4">
            {template.description}
          </p>
          
          {/* AI Reasoning */}
          <div className="bg-dark-surface/80 backdrop-blur-sm rounded-lg p-4 border-l-4 border-neon-cyan mb-6">
            <div className="flex items-start gap-2">
              <svg 
                className="w-5 h-5 text-neon-cyan flex-shrink-0 mt-0.5" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              <div>
                <p className="text-xs font-semibold text-neon-cyan mb-1">Why this works for you:</p>
                <p className="text-sm text-gray-300 leading-relaxed">
                  {reasoning}
                </p>
              </div>
            </div>
          </div>
          
          {/* Select Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onSelect}
            className="w-full bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy font-bold py-4 rounded-xl shadow-glow-cyan hover:shadow-glow-cyan transition-all duration-200"
          >
            <span className="flex items-center justify-center gap-2">
              Select This Template
              <svg 
                className="w-5 h-5" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </svg>
            </span>
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
};
