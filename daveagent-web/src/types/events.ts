/**
 * TypeScript types for DaveAgent WebSocket events
 *
 * These types match the events emitted by the Python backend
 * (see: src/api/event_emitter.py)
 */

/**
 * Base event - all events extend from this
 */
export interface BaseEvent {
  type: string;
  timestamp: string;
}

/**
 * Connection established event
 */
export interface ConnectedEvent extends BaseEvent {
  type: 'connected';
  version: string;
  session_id: string | null;
}

/**
 * Agent message event - Final response from an agent
 */
export interface AgentMessageEvent extends BaseEvent {
  type: 'agent_message';
  agent: string;
  content: string;
}

/**
 * Thinking event - Agent is reasoning/planning
 */
export interface ThinkingEvent extends BaseEvent {
  type: 'thinking';
  agent: string;
  content: string;
}

/**
 * Tool call event - Agent is calling a tool
 */
export interface ToolCallEvent extends BaseEvent {
  type: 'tool_call';
  agent: string;
  tool_name: string;
  tool_args: Record<string, any>;
}

/**
 * Tool result event - Result from tool execution
 */
export interface ToolResultEvent extends BaseEvent {
  type: 'tool_result';
  agent: string;
  tool_name: string;
  result: string;
  success: boolean;
}

/**
 * Code display event - Show code with syntax highlighting
 */
export interface CodeEvent extends BaseEvent {
  type: 'code';
  code: string;
  filename?: string;
  language?: string;
}

/**
 * Diff display event - Show git-style diff
 */
export interface DiffEvent extends BaseEvent {
  type: 'diff';
  diff: string;
  filename?: string;
}

/**
 * Error event
 */
export interface ErrorEvent extends BaseEvent {
  type: 'error';
  message: string;
  context?: string;
}

/**
 * Success event
 */
export interface SuccessEvent extends BaseEvent {
  type: 'success';
  message: string;
}

/**
 * Info event
 */
export interface InfoEvent extends BaseEvent {
  type: 'info';
  message: string;
  prefix?: string;
}

/**
 * Warning event
 */
export interface WarningEvent extends BaseEvent {
  type: 'warning';
  message: string;
}

/**
 * Help event - Structured help information
 */
export interface HelpEvent extends BaseEvent {
  type: 'help';
  sections: Array<{
    title: string;
    icon: string;
    commands: Array<{
      cmd: string;
      desc: string;
    }>;
  }>;
}

/**
 * Session event - Session state changed
 */
export interface SessionEvent extends BaseEvent {
  type: 'session';
  action: 'loaded' | 'saved' | 'created';
  session_id: string;
  metadata?: Record<string, any>;
}

/**
 * Banner event - Show welcome banner
 */
export interface BannerEvent extends BaseEvent {
  type: 'banner';
}

/**
 * User message event - Echo of user's input
 */
export interface UserMessageEvent extends BaseEvent {
  type: 'user_message';
  content: string;
}

/**
 * Goodbye event - Farewell message
 */
export interface GoodbyeEvent extends BaseEvent {
  type: 'goodbye';
}

/**
 * Clear screen event
 */
export interface ClearScreenEvent extends BaseEvent {
  type: 'clear_screen';
}

/**
 * Mode change event
 */
export interface ModeChangeEvent extends BaseEvent {
  type: 'mode_change';
  mode: 'agent' | 'chat';
}

/**
 * Sessions list event (response to list_sessions command)
 */
export interface SessionsListEvent extends BaseEvent {
  type: 'sessions_list';
  sessions: Array<{
    session_id: string;
    title?: string;
    created_at?: string;
    last_interaction?: string;
    total_messages?: number;
    tags?: string[];
  }>;
  total: number;
}

/**
 * Union type of all possible events
 */
export type WebSocketEvent =
  | ConnectedEvent
  | AgentMessageEvent
  | ThinkingEvent
  | ToolCallEvent
  | ToolResultEvent
  | CodeEvent
  | DiffEvent
  | ErrorEvent
  | SuccessEvent
  | InfoEvent
  | WarningEvent
  | HelpEvent
  | SessionEvent
  | BannerEvent
  | UserMessageEvent
  | GoodbyeEvent
  | ClearScreenEvent
  | ModeChangeEvent
  | SessionsListEvent;

/**
 * Commands sent from client to server
 */
export interface ExecuteCommand {
  command: 'execute';
  content: string;
}

export interface ListSessionsCommand {
  command: 'list_sessions';
}

export interface LoadSessionCommand {
  command: 'load_session';
  content: string; // session_id
}

export type WebSocketCommand = ExecuteCommand | ListSessionsCommand | LoadSessionCommand;

/**
 * WebSocket connection states
 */
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';
