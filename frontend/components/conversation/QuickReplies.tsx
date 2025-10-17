import { motion } from 'framer-motion';
import { useState } from 'react';

interface QuickRepliesProps {
  options: string[];
  onSelect: (value: string) => void;
}

export const QuickReplies: React.FC<QuickRepliesProps> = ({ options, onSelect }) => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  
  const handleSelect = (option: string) => {
    setSelectedOption(option);
    onSelect(option);
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.4 }}
      className="flex flex-wrap gap-3 mt-4"
    >
      {options.map((option, index) => (
        <motion.button
          key={index}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{
            delay: 0.3 + index * 0.1,
            type: 'spring',
            stiffness: 260,
            damping: 20,
          }}
          whileHover={{
            scale: 1.05,
            boxShadow: '0 0 20px rgba(0, 217, 255, 0.4)',
          }}
          whileTap={{ scale: 0.95 }}
          onClick={() => handleSelect(option)}
          disabled={selectedOption !== null}
          className={`
            px-5 py-3 rounded-full font-medium text-sm
            border-2 transition-all duration-200
            ${selectedOption === option
              ? 'bg-neon-cyan text-dark-navy border-neon-cyan'
              : selectedOption !== null
              ? 'bg-dark-surface/50 text-gray-600 border-gray-700 cursor-not-allowed'
              : 'bg-dark-elevated border-neon-cyan/30 text-neon-cyan hover:border-neon-cyan hover:bg-neon-cyan/10'
            }
          `}
        >
          {option}
        </motion.button>
      ))}
    </motion.div>
  );
};
