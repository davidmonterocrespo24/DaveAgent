/**
 * DaveAgent Web Interface - Main App Component
 */

import { Terminal } from './components/Terminal';
import { useWebSocket } from './hooks/useWebSocket';

// WebSocket server URL (can be configured via env var)
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/agent';

function App() {
  const { events, status, sendMessage } = useWebSocket({
    url: WS_URL,
    autoConnect: true,
    reconnectAttempts: 3,
    reconnectDelay: 2000,
  });

  // Connection status component
  if (status === 'connecting') {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          backgroundColor: '#0d1117',
          color: '#c9d1d9',
          fontFamily: '"JetBrains Mono", "Fira Code", Consolas, monospace',
          fontSize: '16px',
        }}
      >
        <div style={{ marginBottom: '16px', fontSize: '24px' }}>⏳</div>
        <div>Connecting to DaveAgent...</div>
        <div style={{ marginTop: '8px', color: '#6e7681', fontSize: '14px' }}>{WS_URL}</div>
      </div>
    );
  }

  if (status === 'disconnected' || status === 'error') {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          backgroundColor: '#0d1117',
          color: '#ff7b72',
          fontFamily: '"JetBrains Mono", "Fira Code", Consolas, monospace',
          fontSize: '16px',
        }}
      >
        <div style={{ marginBottom: '16px', fontSize: '24px' }}>❌</div>
        <div>Connection {status === 'error' ? 'error' : 'lost'}</div>
        <div style={{ marginTop: '8px', color: '#6e7681', fontSize: '14px' }}>{WS_URL}</div>
        <div style={{ marginTop: '24px', color: '#c9d1d9', fontSize: '14px' }}>
          Refresh the page to reconnect
        </div>
        <div style={{ marginTop: '8px', color: '#6e7681', fontSize: '12px' }}>
          Make sure the server is running: <code style={{ color: '#39c5cf' }}>daveagent --server</code>
        </div>
      </div>
    );
  }

  // Connected - Show terminal
  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        overflow: 'hidden',
        backgroundColor: '#0d1117',
      }}
    >
      <Terminal events={events} onInput={sendMessage} />
    </div>
  );
}

export default App;
