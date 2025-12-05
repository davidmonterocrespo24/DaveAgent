import sys
import os
import asyncio
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
        self.app = DaveAgentCLI(debug=False, model=model_override)
        # Ensure we are in agent mode
        self.app.current_mode = "agente"

    async def solve(self, problem_statement, repo_path):
        current_dir = os.getcwd()
        try:
            os.chdir(repo_path)

            # FORCE CLEAN MEMORY
            daveagent_dir = Path(".daveagent")
            if daveagent_dir.exists():
                import shutil
                print(f"Cleaning previous memory at {daveagent_dir}...")
                try:
                    shutil.rmtree(daveagent_dir)
                except Exception as e:
                    print(f"Warning: Failed to clean .daveagent: {e}")

            # Reset agent state (memory, tools) for the new context
            await self.app._update_agent_tools_for_mode()

            # SKIP INDEXING - Too slow and not necessary for evaluation
            print(f"⚡ Skipping repository indexing for faster evaluation...")

            # Create focused task with explicit instructions
            focused_task = f"""You are a code repair agent. Your ONLY job is to fix the bug described below.

CRITICAL INSTRUCTIONS:
1. Read the relevant files mentioned in the problem
2. Identify the exact bug location
3. Generate the minimal fix using edit_file or write_file
4. Do NOT write summaries, documentation, or explanations
5. Do NOT create test files unless explicitly required
6. FOCUS on generating the patch that fixes the issue

PROBLEM TO SOLVE:
{problem_statement}

Now analyze the problem, locate the bug, and IMMEDIATELY apply the fix to the files."""

            print(f"Solving problem: {problem_statement[:100]}...")
            print("\n" + "="*50)
            print("📝 PROBLEM STATEMENT")
            print("="*50)
            print(problem_statement)
            print("="*50 + "\n")

            task = TextMessage(content=focused_task, source="user")

            # Run the agent with TIMEOUT
            try:
                # Set timeout to 10 minutes (600 seconds)
                print("⏱️  Starting agent with 10-minute timeout...")
                result = await asyncio.wait_for(
                    self.app.main_team.run(task=task),
                    timeout=600.0
                )

                # PRINT INTERACTION HISTORY (condensed)
                print("\n" + "="*50)
                print("🤖 AGENT INTERACTION LOG")
                print("="*50)
                for i, msg in enumerate(result.messages):
                    source = getattr(msg, 'source', 'Unknown')
                    content = getattr(msg, 'content', '')
                    # Truncate long messages
                    if len(content) > 300:
                        content = content[:300] + "... [truncated]"

                    print(f"\n[{i+1}. {source}]")
                    print(f"{content}")
                print("="*50 + "\n")

                print(f"✅ Agent finished. Total messages: {len(result.messages)}")

                # CHECK FOR CHANGES
                import subprocess
                diff_check = subprocess.run(["git", "diff"], capture_output=True, text=True).stdout

                if not diff_check.strip():
                    print("⚠️ No changes detected. Skipping retry to save time.")
                else:
                    print(f"✅ Patch generated ({len(diff_check)} characters)")

            except asyncio.TimeoutError:
                print("⏱️ TIMEOUT: Task exceeded 10 minutes. Moving to next task.")
            except Exception as e:
                print(f"❌ Error during agent execution: {e}")
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
