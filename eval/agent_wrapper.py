import asyncio
import os
import sys
from pathlib import Path

from autogen_agentchat.messages import TextMessage

# Add src to pythonpath
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from src.main import DaveAgentCLI
except ImportError:
    print("Error importing DaveAgentCLI. Make sure 'src' is in pythonpath.")
    sys.exit(1)


class SWESolver:
    def __init__(self, model_override=None):
        # Initialize in headless mode (no interactive CLI) for evaluation
        self.app = DaveAgentCLI(debug=False, model=model_override, headless=True)
        # Ensure we are in agent mode
        self.app.current_mode = "agent"

        # INCREASE tool iteration limit for complex debugging tasks
        # Default is 5, but SWE-bench tasks may need more exploration
        self.app.coder_agent._max_tool_call_depth = 25

    async def solve(self, problem_statement, repo_path):
        current_dir = os.getcwd()
        try:
            print("\n[DEBUG] Starting solve()")
            print(f"[DEBUG] Current dir: {current_dir}")
            print(f"[DEBUG] Target repo_path: {repo_path}")

            os.chdir(repo_path)
            print(f"[DEBUG] Changed to: {os.getcwd()}")

            # FORCE CLEAN MEMORY
            daveagent_dir = Path(".daveagent")
            if daveagent_dir.exists():
                import shutil
                print(f"[DEBUG] Cleaning previous memory at {daveagent_dir}...")
                try:
                    shutil.rmtree(daveagent_dir)
                except Exception as e:
                    print(f"[WARNING] Failed to clean .daveagent: {e}")

            # Reset agent state (memory, tools) for the new context
            print("[DEBUG] Updating agent tools for mode...")
            await self.app._update_agent_tools_for_mode()
            print("[DEBUG] Agent tools updated")

            # INCREASE tool iteration limit AFTER recreating agents
            self.app.coder_agent._max_tool_call_depth = 25
            print("[DEBUG] Set coder max_tool_call_depth to 25")

            # SKIP INDEXING - Too slow and not necessary for evaluation
            print("[EVAL] Skipping repository indexing for faster evaluation...")

            # Create focused task with explicit instructions
            # Include current working directory so agent knows where to look
            abs_repo_path = os.path.abspath(repo_path)
            focused_task = f"""You are a code repair agent. Your ONLY job is to fix the bug described below.

WORKSPACE INFORMATION:
- Current working directory: {abs_repo_path}
- All file paths should be RELATIVE to this directory
- Example: Use "astropy/modeling/separable.py" NOT absolute paths

CRITICAL INSTRUCTIONS:
1. Read the relevant files mentioned in the problem using RELATIVE paths
2. Identify the exact bug location
3. Generate the minimal fix using edit_file with RELATIVE paths
4. Do NOT write summaries, documentation, or explanations
5. Do NOT create test files unless explicitly required
6. FOCUS on generating the patch that fixes the issue
7. Maximum 8 tool calls total - be efficient!

PROBLEM TO SOLVE:
{problem_statement}

START NOW: Use list_dir to explore, read_file to find the bug, edit_file to fix it, etc etc."""

            print(f"Solving problem: {problem_statement[:100]}...")
            print("\n" + "=" * 50)
            print("PROBLEM STATEMENT")
            print("=" * 50)
            print(problem_statement)
            print("=" * 50 + "\n")

            task = TextMessage(content=focused_task, source="user")

            # Run the agent with TIMEOUT
            try:
                # Set timeout to 10 minutes (600 seconds)
                print("[DEBUG] Creating task message...")
                print(f"[DEBUG] Task content length: {len(focused_task)} chars")
                print(f"[DEBUG] main_team type: {type(self.app.main_team)}")
                print(
                    f"[DEBUG] main_team participants: {len(self.app.main_team._participants) if hasattr(self.app.main_team, '_participants') else 'unknown'}")

                print("\n[EVAL] Starting agent with 10-minute timeout...")
                print("[DEBUG] Calling main_team.run()...")

                result = await asyncio.wait_for(
                    self.app.main_team.run(task=task),
                    timeout=1600.0
                )

                print("[DEBUG] main_team.run() completed")
                print(f"[DEBUG] Result type: {type(result)}")
                print(f"[DEBUG] Result has messages: {hasattr(result, 'messages')}")

                # PRINT INTERACTION HISTORY - WITH DETAILED LOGGING
                print("\n[EVAL] Agent completed conversation")
                print(f"[EVAL] Total messages exchanged: {len(result.messages)}")

                # Print each message for debugging
                print("\n[DEBUG] ===== MESSAGE DETAILS =====")
                for i, msg in enumerate(result.messages):
                    source = getattr(msg, 'source', 'Unknown')
                    content = getattr(msg, 'content', '')
                    msg_type = type(msg).__name__

                    print(f"[DEBUG] Message {i + 1}:")
                    print(f"  - Source: {source}")
                    print(f"  - Type: {msg_type}")
                    print(f"  - Content length: {len(str(content))} chars")
                    print(f"  - Content preview: {str(content)[:200]}")
                print("[DEBUG] ===== END MESSAGE DETAILS =====\n")

                print(f"[SUCCESS] Agent finished. Total messages: {len(result.messages)}")

                # CHECK FOR CHANGES
                import subprocess
                diff_check = subprocess.run(["git", "diff"], capture_output=True, text=True).stdout

                if not diff_check.strip():
                    print("[WARNING] No changes detected. Skipping retry to save time.")
                else:
                    print(f"[SUCCESS] Patch generated ({len(diff_check)} characters)")

            except asyncio.TimeoutError:
                print("[TIMEOUT] Task exceeded 20 minutes. Moving to next task.")
            except Exception as e:
                print(f"[ERROR] Error during agent execution: {e}")
                import traceback
                traceback.print_exc()

            print("Task execution finished.")

        except Exception as e:
            print(f"Error solving task: {e}")
            import traceback
            traceback.print_exc()
        finally:
            os.chdir(current_dir)

    async def close(self):
        try:
            if hasattr(self.app, 'model_client'):
                await self.app.model_client.close()
            if hasattr(self.app, 'memory_manager'):
                await self.app.memory_manager.close()
            if hasattr(self.app, 'state_manager'):
                await self.app.state_manager.close()
        except Exception as e:
            print(f"Error closing resources: {e}")
