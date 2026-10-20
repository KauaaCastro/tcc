import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
// @ts-expect-error CSS side-effect import is handled by the bundler.
import './styles/theme.css';
// @ts-expect-error CSS side-effect import is handled by the bundler.
import './styles/global.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
