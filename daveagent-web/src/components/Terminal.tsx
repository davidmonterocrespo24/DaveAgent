/**
 * Terminal component using xterm.js
 * Renders a terminal that displays DaveAgent events
 */

import { useEffect, useRef } from 'react';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import '@xterm/xterm/css/xterm.css';
import { WebSocketEvent } from '../types/events';
import { renderEvent } from '../utils/eventRenderer';

interface TerminalProps {
  events: WebSocketEvent[];
  onInput: (input: string) => void;
}

/**
 * Terminal component that displays DaveAgent output
 *
 * Features:
 * - Full xterm.js terminal emulation
 * - Supports ANSI colors
 * - Command history (arrow keys)
 * - Copy/paste support
 * - Clickable links
 *
 * @param events - Array of WebSocket events to display
 * @param onInput - Callback when user submits input
 */
export function Terminal({ events, onInput }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const inputBufferRef = useRef<string>('');
  const historyRef = useRef<string[]>([]);
  const historyIndexRef = useRef<number>(-1);

  // Initialize xterm.js
  useEffect(() => {
    if (!terminalRef.current) return;

    console.log('[Terminal] Initializing xterm.js...');

    // Create terminal with DaveAgent theme
    const xterm = new XTerm({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", Consolas, monospace',
      theme: {
        background: '#0d1117',
        foreground: '#c9d1d9',
        cursor: '#58a6ff',
        cursorAccent: '#0d1117',
        selectionBackground: '#1f6feb4d',
        selectionForeground: '#c9d1d9',
        black: '#484f58',
        red: '#ff7b72',
        green: '#3fb950',
        yellow: '#d29922',
        blue: '#58a6ff',
        magenta: '#bc8cff',
        cyan: '#39c5cf',
        white: '#b1bac4',
        brightBlack: '#6e7681',
        brightRed: '#ffa198',
        brightGreen: '#56d364',
        brightYellow: '#e3b341',
        brightBlue: '#79c0ff',
        brightMagenta: '#d2a8ff',
        brightCyan: '#56d4dd',
        brightWhite: '#f0f6fc',
      },
      rows: 30,
      cols: 120,
      scrollback: 10000,
      allowProposedApi: true,
    });

    // Add addons
    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();

    xterm.loadAddon(fitAddon);
    xterm.loadAddon(webLinksAddon);

    // Open terminal
    xterm.open(terminalRef.current);
    fitAddon.fit();

    xtermRef.current = xterm;
    fitAddonRef.current = fitAddon;

    console.log('[Terminal] xterm.js initialized');

    // Handle user input
    xterm.onData((data) => {
      const code = data.charCodeAt(0);

      // Enter key (0x0D = \r)
      if (code === 0x0d) {
        if (inputBufferRef.current.trim()) {
          // Add to history
          historyRef.current.push(inputBufferRef.current);
          historyIndexRef.current = historyRef.current.length;

          // Send to backend
          onInput(inputBufferRef.current);

          // Clear input buffer
          inputBufferRef.current = '';
        }
        xterm.write('\r\n');
        return;
      }

      // Backspace (0x7F)
      if (code === 0x7f) {
        if (inputBufferRef.current.length > 0) {
          inputBufferRef.current = inputBufferRef.current.slice(0, -1);
          xterm.write('\b \b');
        }
        return;
      }

      // Ctrl+C (0x03)
      if (code === 0x03) {
        inputBufferRef.current = '';
        xterm.write('^C\r\n\x1b[36mYou:\x1b[0m ');
        return;
      }

      // Ctrl+L (0x0C) - Clear screen
      if (code === 0x0c) {
        xterm.clear();
        xterm.write('\x1b[36mYou:\x1b[0m ');
        return;
      }

      // Arrow Up (0x1B5B41) - Previous command in history
      if (data === '\x1b[A') {
        if (historyIndexRef.current > 0) {
          historyIndexRef.current--;
          const historyCommand = historyRef.current[historyIndexRef.current];

          // Clear current line
          xterm.write('\r\x1b[K\x1b[36mYou:\x1b[0m ');

          // Write history command
          xterm.write(historyCommand);
          inputBufferRef.current = historyCommand;
        }
        return;
      }

      // Arrow Down (0x1B5B42) - Next command in history
      if (data === '\x1b[B') {
        if (historyIndexRef.current < historyRef.current.length - 1) {
          historyIndexRef.current++;
          const historyCommand = historyRef.current[historyIndexRef.current];

          // Clear current line
          xterm.write('\r\x1b[K\x1b[36mYou:\x1b[0m ');

          // Write history command
          xterm.write(historyCommand);
          inputBufferRef.current = historyCommand;
        } else if (historyIndexRef.current === historyRef.current.length - 1) {
          historyIndexRef.current = historyRef.current.length;

          // Clear current line
          xterm.write('\r\x1b[K\x1b[36mYou:\x1b[0m ');
          inputBufferRef.current = '';
        }
        return;
      }

      // Printable characters (0x20 to 0x7E)
      if (code >= 0x20 && code <= 0x7e) {
        inputBufferRef.current += data;
        xterm.write(data);
        return;
      }

      // Ignore other control characters
    });

    // Handle window resize
    const handleResize = () => {
      fitAddon.fit();
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      console.log('[Terminal] Disposing xterm.js...');
      window.removeEventListener('resize', handleResize);
      xterm.dispose();
    };
  }, [onInput]);

  // Render events as they come in
  useEffect(() => {
    const xterm = xtermRef.current;
    if (!xterm || events.length === 0) return;

    // Get the latest event
    const latestEvent = events[events.length - 1];
    console.log('[Terminal] Rendering event:', latestEvent.type);

    // Render the event
    renderEvent(xterm, latestEvent);
  }, [events]);

  return (
    <div
      ref={terminalRef}
      style={{
        width: '100%',
        height: '100vh',
        padding: '8px',
        backgroundColor: '#0d1117',
        overflow: 'hidden',
      }}
    />
  );
}
