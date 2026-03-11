/**
 * Event renderer - Converts WebSocket events to terminal output
 *
 * This module handles rendering all DaveAgent events to the xterm.js terminal
 * using ANSI escape codes for colors and formatting.
 */

import { Terminal } from '@xterm/xterm';
import { WebSocketEvent } from '../types/events';

/**
 * ANSI color codes for terminal output
 */
const ANSI = {
  // Reset
  RESET: '\x1b[0m',

  // Regular colors
  BLACK: '\x1b[30m',
  RED: '\x1b[31m',
  GREEN: '\x1b[32m',
  YELLOW: '\x1b[33m',
  BLUE: '\x1b[34m',
  MAGENTA: '\x1b[35m',
  CYAN: '\x1b[36m',
  WHITE: '\x1b[37m',

  // Bright colors
  BRIGHT_BLACK: '\x1b[90m',
  BRIGHT_RED: '\x1b[91m',
  BRIGHT_GREEN: '\x1b[92m',
  BRIGHT_YELLOW: '\x1b[93m',
  BRIGHT_BLUE: '\x1b[94m',
  BRIGHT_MAGENTA: '\x1b[95m',
  BRIGHT_CYAN: '\x1b[96m',
  BRIGHT_WHITE: '\x1b[97m',

  // Text formatting
  BOLD: '\x1b[1m',
  DIM: '\x1b[2m',
  UNDERLINE: '\x1b[4m',
};

/**
 * DaveAgent ASCII banner (same as CLI)
 */
const BANNER = `\x1b[35m╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗  █████╗ ██╗   ██╗███████╗                          ║
║   ██╔══██╗██╔══██╗██║   ██║██╔════╝                          ║
║   ██║  ██║███████║██║   ██║█████╗                            ║
║   ██║  ██║██╔══██║╚██╗ ██╔╝██╔══╝                            ║
║   ██████╔╝██║  ██║ ╚████╔╝ ███████╗                          ║
║   ╚═════╝ ╚═╝  ╚═╝  ╚═══╝  ╚══════╝                          ║
║                                                              ║
║    █████╗  ██████╗ ███████╗███╗   ██╗████████╗               ║
║   ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝               ║
║   ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║                  ║
║   ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║                  ║
║   ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║                  ║
║   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝                  ║
║                                                              ║
║              Intelligent Development Agent                   ║
║                    Web Interface                             ║
╚══════════════════════════════════════════════════════════════╝\x1b[0m`;

/**
 * Render a WebSocket event to the terminal
 *
 * @param terminal - xterm.js Terminal instance
 * @param event - WebSocket event to render
 */
export function renderEvent(terminal: Terminal, event: WebSocketEvent): void {
  switch (event.type) {
    case 'connected':
      renderConnected(terminal, event);
      break;

    case 'banner':
      renderBanner(terminal);
      break;

    case 'agent_message':
      renderAgentMessage(terminal, event);
      break;

    case 'thinking':
      renderThinking(terminal, event);
      break;

    case 'tool_call':
      renderToolCall(terminal, event);
      break;

    case 'tool_result':
      renderToolResult(terminal, event);
      break;

    case 'code':
      renderCode(terminal, event);
      break;

    case 'diff':
      renderDiff(terminal, event);
      break;

    case 'error':
      renderError(terminal, event);
      break;

    case 'success':
      renderSuccess(terminal, event);
      break;

    case 'info':
      renderInfo(terminal, event);
      break;

    case 'warning':
      renderWarning(terminal, event);
      break;

    case 'help':
      renderHelp(terminal, event);
      break;

    case 'session':
      renderSession(terminal, event);
      break;

    case 'user_message':
      // User messages are already shown via input, skip
      break;

    case 'goodbye':
      renderGoodbye(terminal);
      break;

    case 'clear_screen':
      terminal.clear();
      break;

    case 'mode_change':
      renderModeChange(terminal, event);
      break;

    case 'sessions_list':
      renderSessionsList(terminal, event);
      break;

    default:
      // Unknown event type, log for debugging
      console.warn('[Terminal] Unknown event type:', (event as any).type);
      terminal.writeln(`${ANSI.YELLOW}[Unknown event: ${(event as any).type}]${ANSI.RESET}`);
  }
}

function renderConnected(terminal: Terminal, event: any): void {
  renderBanner(terminal);
  terminal.writeln('');
  terminal.writeln(`${ANSI.GREEN}✓ Connected to DaveAgent v${event.version}${ANSI.RESET}`);
  terminal.writeln(`${ANSI.BLUE}ℹ Type /help for available commands${ANSI.RESET}`);
  terminal.writeln('');
  terminal.write(`${ANSI.CYAN}You:${ANSI.RESET} `);
}

function renderBanner(terminal: Terminal): void {
  terminal.writeln(BANNER);
}

function renderAgentMessage(terminal: Terminal, event: any): void {
  terminal.writeln('');
  terminal.writeln(`${ANSI.GREEN}${event.agent}:${ANSI.RESET} ${event.content}`);
  terminal.writeln('');
  terminal.write(`${ANSI.CYAN}You:${ANSI.RESET} `);
}

function renderThinking(terminal: Terminal, event: any): void {
  terminal.writeln(`${ANSI.BRIGHT_BLACK}💭 ${event.agent}: ${event.content}${ANSI.RESET}`);
}

function renderToolCall(terminal: Terminal, event: any): void {
  const args = JSON.stringify(event.tool_args);
  const argsPreview = args.length > 100 ? args.substring(0, 100) + '...' : args;
  terminal.writeln(
    `${ANSI.YELLOW}🔧 ${event.agent} > ${event.tool_name}${ANSI.RESET} ${ANSI.BRIGHT_BLACK}${argsPreview}${ANSI.RESET}`
  );
}

function renderToolResult(terminal: Terminal, event: any): void {
  const icon = event.success ? '✅' : '❌';
  const color = event.success ? ANSI.GREEN : ANSI.RED;
  const resultPreview =
    event.result.length > 200 ? event.result.substring(0, 200) + '...' : event.result;
  terminal.writeln(`${color}${icon} ${event.tool_name}:${ANSI.RESET} ${resultPreview}`);
}

function renderCode(terminal: Terminal, event: any): void {
  if (event.filename) {
    terminal.writeln('');
    terminal.writeln(`${ANSI.CYAN}${'─'.repeat(60)}${ANSI.RESET}`);
    terminal.writeln(`${ANSI.CYAN}📄 ${event.filename}${ANSI.RESET}`);
    terminal.writeln(`${ANSI.CYAN}${'─'.repeat(60)}${ANSI.RESET}`);
  }

  // Split code into lines and render
  const lines = event.code.split('\n');
  lines.forEach((line: string) => {
    terminal.writeln(line);
  });

  if (event.filename) {
    terminal.writeln(`${ANSI.CYAN}${'─'.repeat(60)}${ANSI.RESET}`);
    terminal.writeln('');
  }
}

function renderDiff(terminal: Terminal, event: any): void {
  if (event.filename) {
    terminal.writeln('');
    terminal.writeln(`${ANSI.CYAN}📝 Diff: ${event.filename}${ANSI.RESET}`);
  }

  // Render diff with colors
  const lines = event.diff.split('\n');
  lines.forEach((line: string) => {
    if (line.startsWith('+')) {
      terminal.writeln(`${ANSI.GREEN}${line}${ANSI.RESET}`);
    } else if (line.startsWith('-')) {
      terminal.writeln(`${ANSI.RED}${line}${ANSI.RESET}`);
    } else if (line.startsWith('@')) {
      terminal.writeln(`${ANSI.CYAN}${line}${ANSI.RESET}`);
    } else {
      terminal.writeln(line);
    }
  });

  terminal.writeln('');
}

function renderError(terminal: Terminal, event: any): void {
  terminal.writeln('');
  terminal.writeln(`${ANSI.RED}✗ Error: ${event.message}${ANSI.RESET}`);
  if (event.context) {
    terminal.writeln(`${ANSI.BRIGHT_BLACK}  Context: ${event.context}${ANSI.RESET}`);
  }
  terminal.writeln('');
}

function renderSuccess(terminal: Terminal, event: any): void {
  terminal.writeln(`${ANSI.GREEN}✓ ${event.message}${ANSI.RESET}`);
}

function renderInfo(terminal: Terminal, event: any): void {
  const prefix = event.prefix ? `${event.prefix}: ` : 'ℹ ';
  terminal.writeln(`${ANSI.BLUE}${prefix}${event.message}${ANSI.RESET}`);
}

function renderWarning(terminal: Terminal, event: any): void {
  terminal.writeln(`${ANSI.YELLOW}⚠ ${event.message}${ANSI.RESET}`);
}

function renderHelp(terminal: Terminal, event: any): void {
  terminal.writeln('');
  terminal.writeln(`${ANSI.MAGENTA}╔══════════════════════════════════════════════════════════════╗${ANSI.RESET}`);
  terminal.writeln(`${ANSI.MAGENTA}║                    DAVEAGENT COMMANDS                        ║${ANSI.RESET}`);
  terminal.writeln(`${ANSI.MAGENTA}╚══════════════════════════════════════════════════════════════╝${ANSI.RESET}`);
  terminal.writeln('');

  event.sections.forEach((section: any) => {
    terminal.writeln(`${ANSI.BOLD}${section.icon} ${section.title}:${ANSI.RESET}`);
    section.commands.forEach((cmd: any) => {
      terminal.writeln(`  ${ANSI.CYAN}${cmd.cmd.padEnd(25)}${ANSI.RESET} - ${cmd.desc}`);
    });
    terminal.writeln('');
  });
}

function renderSession(terminal: Terminal, event: any): void {
  const actionText = {
    loaded: 'Session loaded',
    saved: 'Session saved',
    created: 'Session created',
  }[event.action] || 'Session updated';

  terminal.writeln(`${ANSI.GREEN}✓ ${actionText}: ${event.session_id}${ANSI.RESET}`);

  if (event.metadata) {
    if (event.metadata.title) {
      terminal.writeln(`  ${ANSI.BRIGHT_BLACK}Title: ${event.metadata.title}${ANSI.RESET}`);
    }
    if (event.metadata.total_messages) {
      terminal.writeln(`  ${ANSI.BRIGHT_BLACK}Messages: ${event.metadata.total_messages}${ANSI.RESET}`);
    }
  }
}

function renderGoodbye(terminal: Terminal): void {
  terminal.writeln('');
  terminal.writeln(`${ANSI.MAGENTA}👋 Thank you for using DaveAgent!${ANSI.RESET}`);
  terminal.writeln('');
}

function renderModeChange(terminal: Terminal, event: any): void {
  const modeText = event.mode === 'agent' ? 'AGENT (full tools)' : 'CHAT (read-only)';
  terminal.writeln(`${ANSI.BLUE}ℹ Mode changed to: ${modeText}${ANSI.RESET}`);
}

function renderSessionsList(terminal: Terminal, event: any): void {
  terminal.writeln('');
  terminal.writeln(`${ANSI.BOLD}📊 Saved Sessions (${event.total}):${ANSI.RESET}`);
  terminal.writeln('');

  if (event.sessions.length === 0) {
    terminal.writeln(`${ANSI.BRIGHT_BLACK}  No sessions found${ANSI.RESET}`);
  } else {
    event.sessions.forEach((session: any, index: number) => {
      const title = session.title || 'Untitled';
      const messages = session.total_messages || 0;
      const date = session.last_interaction
        ? new Date(session.last_interaction).toLocaleString()
        : 'Unknown';

      terminal.writeln(`${ANSI.CYAN}${(index + 1).toString().padStart(3)}. ${session.session_id}${ANSI.RESET}`);
      terminal.writeln(`     ${ANSI.BRIGHT_BLACK}Title: ${title}${ANSI.RESET}`);
      terminal.writeln(`     ${ANSI.BRIGHT_BLACK}Messages: ${messages} | Last: ${date}${ANSI.RESET}`);
      terminal.writeln('');
    });
  }

  terminal.writeln(`${ANSI.BLUE}💡 Use /load-session <id> to load a session${ANSI.RESET}`);
  terminal.writeln('');
}
