import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { Send, Bot, User, Loader } from 'lucide-react';
import { chatAPI } from '../services/api';

const Container = styled.div`
  width: 100%;
  max-width: 800px;
  height: 600px;
  background: white;
  border-radius: 1rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const Header = styled.div`
  background: ${props => props.theme?.colors?.primary || '#4f46e5'};
  color: white;
  padding: 1.5rem;
  text-align: center;
`;

const MessagesArea = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background: #f9fafb;
`;

const MessageRow = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  flex-direction: ${props => (props.$isUser ? 'row-reverse' : 'row')};
`;

const Avatar = styled.div`
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: ${props =>
    props.$isUser ? '#6b7280' : props.theme?.colors?.primary || '#4f46e5'};
`;

const Bubble = styled.div`
  max-width: 75%;
  padding: 0.65rem 0.9rem;
  border-radius: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  color: ${props => (props.$isUser ? 'white' : '#111827')};
  background: ${props =>
    props.$isUser
      ? props.theme?.colors?.primary || '#4f46e5'
      : props.$isError
      ? '#fee2e2'
      : 'white'};
  border: ${props => (props.$isUser ? 'none' : '1px solid #e5e7eb')};
`;

const InputArea = styled.div`
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid #e5e7eb;
  background: white;
`;

const TextInput = styled.textarea`
  flex: 1;
  resize: none;
  max-height: 120px;
  padding: 0.65rem 0.9rem;
  font: inherit;
  border: 1px solid #d1d5db;
  border-radius: 0.75rem;

  &:focus {
    outline: 2px solid ${props => props.theme?.colors?.primary || '#4f46e5'};
    outline-offset: 0;
  }

  &:disabled {
    background: #f3f4f6;
  }
`;

const SendButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  border: none;
  border-radius: 0.75rem;
  color: white;
  cursor: pointer;
  background: ${props => props.theme?.colors?.primary || '#4f46e5'};

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ChatContainer = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hello! I'm your AI assistant. What would you like to learn about Python and AI?",
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef(null);

  // Scroll to the newest message whenever the list or loading state changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async () => {
    const text = inputMessage.trim();
    if (!text || isLoading) return;

    const userMessage = { role: 'user', content: text };

    // History sent to the backend = everything BEFORE the new message
    const history = messages;

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(text, history);

      if (response.success) {
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: response.response },
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: response.error_message || response.response,
            isError: true,
          },
        ]);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Could not reach the server. Check that the backend is running on port 8000.',
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Enter sends, Shift+Enter adds a new line
  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Container>
      <Header>
        <h1>AI Chat Assistant</h1>
        <p>Powered by Python & Gemini AI - Day 1 Project</p>
      </Header>

      <MessagesArea>
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <MessageRow key={index} $isUser={isUser}>
              <Avatar $isUser={isUser}>
                {isUser ? <User size={16} /> : <Bot size={16} />}
              </Avatar>
              <Bubble $isUser={isUser} $isError={msg.isError}>
                {msg.content}
              </Bubble>
            </MessageRow>
          );
        })}

        {isLoading && (
          <MessageRow $isUser={false}>
            <Avatar $isUser={false}>
              <Loader size={16} />
            </Avatar>
            <Bubble $isUser={false}>Thinking...</Bubble>
          </MessageRow>
        )}

        <div ref={bottomRef} />
      </MessagesArea>

      <InputArea>
        <TextInput
          rows={1}
          value={inputMessage}
          onChange={e => setInputMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message and press Enter..."
          disabled={isLoading}
          aria-label="Message"
        />
        <SendButton
          onClick={handleSendMessage}
          disabled={isLoading || !inputMessage.trim()}
          aria-label="Send message"
        >
          <Send size={18} />
        </SendButton>
      </InputArea>
    </Container>
  );
};

export default ChatContainer;
