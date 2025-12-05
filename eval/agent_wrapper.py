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
            
            # Reset agent state (memory, tools) for the new context
            # This effectively clears memory and re-indexes if we call index later
            await self.app._update_agent_tools_for_mode()
            
            # Index the repo
            print(f"Indexing repository at {repo_path}...")
            await self.app._index_project()
            
            print(f"Solving problem: {problem_statement[:100]}...")
            task = TextMessage(content=problem_statement, source="user")
            
            # Run the agent
            # We need to collect the stream or just let it finish
            # The agent loop usually terminates with 'TASK_COMPLETED' or max messages
            # We wrap in a timeout just in case
            # Run the agent using .run() which might be more stable than run_stream with current autogen version
            try:
                # Capture result
                result = await self.app.main_team.run(task=task)
                
                # PRINT INTERACTION HISTORY
                print("\n" + "="*50)
                print("🤖 AGENT INTERACTION LOG")
                print("="*50)
                for msg in result.messages:
                    source = getattr(msg, 'source', 'Unknown')
                    content = getattr(msg, 'content', '')
                    # Try to get models usage if available (for cost tracking)
                    models_usage = getattr(msg, 'models_usage', None)
                    
                    print(f"\n[{source}]")
                    print("-" * 20)
                    print(f"{content}")
                    if models_usage:
                        print(f"[Usage: {models_usage}]")
                print("="*50 + "\n")

                print(f"Agent finished. Result messages: {len(result.messages)}")
                
                # CHECK FOR CHANGES
                import subprocess
                diff_check = subprocess.run(["git", "diff"], capture_output=True, text=True).stdout
                
                if not diff_check.strip():
                    print("⚠️ No changes detected. Prompting agent to apply fix...")
                    retry_msg = TextMessage(content="I don't see any changes in the file system. You MUST use 'edit_file' or 'write_file' to apply your fix to the actual files. Please apply the fix now.", source="user")
                    result = await self.app.main_team.run(task=retry_msg)
                    print(f"Retry finished. Result messages: {len(result.messages)}")
                
                # Show last message if available
                if result.messages:
                    last_msg = result.messages[-1]
                    content = getattr(last_msg, 'content', 'No content')
                    print(f"Final response: {str(content)[:200]}...")
            except Exception as e:
                print(f"Error during agent execution: {e}")

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
