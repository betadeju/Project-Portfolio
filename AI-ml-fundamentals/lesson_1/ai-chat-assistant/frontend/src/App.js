import React from 'react';
import { ThemeProvider } from 'styled-components';
import { GlobalStyles, theme } from './styles/GlobalStyles';
import ChatContainer from './components/ChatContainer';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <GlobalStyles />
      <ChatContainer />
    </ThemeProvider>
  );
}

export default App;