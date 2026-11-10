import { createGlobalStyle } from 'styled-components';

export const GlobalStyles = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #333;
    min-height: 100vh;
  }

  #root {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
`;

export const theme = {
  colors: {
    primary: '#4f46e5',
    secondary: '#10b981',
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#1f2937',
    border: '#e5e7eb',
  },
  shadows: {
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
  },
  borderRadius: {
    lg: '0.5rem',
    xl: '0.75rem',
  },
};