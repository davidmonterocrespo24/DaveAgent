"""
Manager for reporting errors as GitHub issues.
Uses GitHub CLI (gh) to create issues with LLM-generated titles.
"""

import subprocess
import traceback
import sys
from typing import Optional
from src.utils import get_logger

class IssueReporter:
    """
    Handles automatic creation of GitHub issues for unhandled exceptions.
    """

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.repo = "davidmonterocrespo24/DaveAgent"

    async def report_error(self, exception: Exception, context: str, model_client=None) -> bool:
        """
        Creates a GitHub issue for the given exception.
        
        Args:
            exception: The exception object
            context: Description of where the error occurred
            model_client: Client to generate issue title (optional)
            
        Returns:
            bool: True if issue was created successfully
        """
        try:
            self.logger.info("🚨 Initiating automatic error reporting...")
            
            # 1. Capture Traceback
            tb = traceback.format_exc()
            if not tb or tb == "NoneType: None\n":
                # If no active exception, try to format the passed exception
                tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

            # 2. Generate Title using LLM
            title = f"Bug: Unhandled error in {context}"
            if model_client:
                try:
                    prompt = (
                        f"Given this python error traceback, generate a concise, descriptive GitHub issue title "
                        f"(max 80 chars). Do not use quotes. Error: {str(exception)}"
                    )
                    # We use a simple create call. We assume model_client has a create method 
                    # compatible with the one used in the rest of the app (OpenAIChatCompletionClient)
                    # Note: We need to check the actual interface.
                    # Using a simplified approach if it's the standard wrapper
                    
                    # Construct a simple message list for the chat completion
                    messages = [{"role": "user", "content": prompt}]
                    
                    # Depending on the client type, the call might differ slightly.
                    # We'll try the standard create method.
                    response = await model_client.create(messages)
                    if response and response.content:
                        generated_title = response.content.strip()
                        # Sanitize title
                        generated_title = generated_title.replace('"', '').replace("'", "")
                        title = f"Bug: {generated_title}"
                        
                except Exception as e:
                    self.logger.warning(f"Failed to generate AI title: {e}")

            # 3. Construct Body
            body = f"""
## 🚨 Automatic Error Report

**Context:** `{context}`
**Type:** `{type(exception).__name__}`
**Message:** `{str(exception)}`

### Traceback
```python
{tb}
```

*Reported automatically by DaveAgent.*
"""

            # 4. Create Issue via gh CLI
            self.logger.info(f"Creating issue in {self.repo}: {title}")
            
            # Checks if gh is installed/authenticated
            check = subprocess.run(["gh", "--version"], capture_output=True, text=True)
            if check.returncode != 0:
                self.logger.error("GitHub CLI (gh) not found or not working.")
                return False

            cmd = [
                "gh", "issue", "create",
                "--repo", self.repo,
                "--title", title,
                "--body", body,
                "--label", "bug,auto-report"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                self.logger.info(f"✅ Issue created successfully: {result.stdout.strip()}")
                return True
            else:
                self.logger.error(f"Failed to create issue: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to report error: {e}")
            return False
