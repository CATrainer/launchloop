import { create } from 'zustand';

interface Message {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  messageType: 'text' | 'quick_replies' | 'template_selection' | 'thinking' | 'generation_progress';
  quickReplies?: string[];
  templates?: any[];
  thinkingStatus?: string;
  timestamp: Date;
}

interface ConversationState {
  conversationId: string | null;
  messages: Message[];
  isAIResponding: boolean;
  streamingMessageId: string | null;
  currentStreamedText: string;
  
  // Actions
  setConversationId: (id: string) => void;
  addUserMessage: (content: string) => void;
  startAIResponse: () => void;
  updateStreamedText: (messageId: string, text: string) => void;
  completeAIMessage: (messageId: string, messageType: string, data?: any) => void;
  stopAIResponse: () => void;
  clearConversation: () => void;
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  conversationId: null,
  messages: [],
  isAIResponding: false,
  streamingMessageId: null,
  currentStreamedText: '',
  
  setConversationId: (id) => set({ conversationId: id }),
  
  addUserMessage: (content) => {
    const newMessage: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content,
      messageType: 'text',
      timestamp: new Date(),
    };
    
    set((state) => ({
      messages: [...state.messages, newMessage],
    }));
  },
  
  startAIResponse: () => {
    const messageId = `ai-${Date.now()}`;
    
    const newMessage: Message = {
      id: messageId,
      sender: 'ai',
      content: '',
      messageType: 'text',
      timestamp: new Date(),
    };
    
    set((state) => ({
      messages: [...state.messages, newMessage],
      isAIResponding: true,
      streamingMessageId: messageId,
      currentStreamedText: '',
    }));
    
    return messageId;
  },
  
  updateStreamedText: (messageId, text) => {
    set((state) => {
      const messages = state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, content: text } : msg
      );
      
      return {
        messages,
        currentStreamedText: text,
      };
    });
  },
  
  completeAIMessage: (messageId, messageType, data = {}) => {
    set((state) => {
      const messages = state.messages.map((msg) =>
        msg.id === messageId
          ? {
              ...msg,
              messageType: messageType as any,
              quickReplies: data.quick_replies,
              templates: data.templates,
              thinkingStatus: data.thinking_status,
            }
          : msg
      );
      
      return {
        messages,
        isAIResponding: false,
        streamingMessageId: null,
        currentStreamedText: '',
      };
    });
  },
  
  stopAIResponse: () => {
    set({
      isAIResponding: false,
      streamingMessageId: null,
      currentStreamedText: '',
    });
  },
  
  clearConversation: () => {
    set({
      conversationId: null,
      messages: [],
      isAIResponding: false,
      streamingMessageId: null,
      currentStreamedText: '',
    });
  },
}));
