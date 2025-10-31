# Importa el decorador de herramientas desde el ADK de watsonx Orchestrate
from ibm_watsonx_orchestrate.agent_builder.tools import tool

@tool
def edit_file(target_file: str, instructions: str, code_edit: str, explanation: str = "") -> str:
    """
    Apply edits to an existing file using the // ... existing code ... marker system.
    
    Parameters:
        target_file (str): Path to the file to be edited
        instructions (str): Description of the changes to be made
        code_edit (str): The new code content with markers indicating where existing code should be preserved
        explanation (str): Optional explanation for the edit operation
    
    Returns:
        str: Success message with edit summary or error message if operation failed
    """
    try:
        # Read the current file
        with open(target_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Parse the code_edit to find the edits and markers
        lines = code_edit.split('\n')
        new_content = ""
        original_lines = original_content.split('\n')
        current_line_index = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this is an "existing code" marker
            if "... existing code ..." in line or "existing code" in line:
                # Find the next non-marker line to determine how much to skip
                next_edit_line = None
                for j in range(i + 1, len(lines)):
                    if "... existing code ..." not in lines[j] and lines[j].strip():
                        next_edit_line = lines[j]
                        break
                
                # If we have a next edit line, find it in the original content
                if next_edit_line:
                    # Look for the next edit line in the original content
                    found_index = -1
                    for k in range(current_line_index, len(original_lines)):
                        if next_edit_line.strip() in original_lines[k] or original_lines[k].strip() == next_edit_line.strip():
                            found_index = k
                            break
                    
                    if found_index != -1:
                        # Add the skipped original lines
                        for k in range(current_line_index, found_index):
                            new_content += original_lines[k] + '\n'
                        current_line_index = found_index
                    else:
                        # If we can't find the next line, add some original content
                        skip_lines = min(5, len(original_lines) - current_line_index)
                        for k in range(current_line_index, current_line_index + skip_lines):
                            if k < len(original_lines):
                                new_content += original_lines[k] + '\n'
                        current_line_index += skip_lines
                else:
                    # No next edit line found, skip to end or add remaining original content
                    remaining_lines = min(10, len(original_lines) - current_line_index)
                    for k in range(current_line_index, current_line_index + remaining_lines):
                        if k < len(original_lines):
                            new_content += original_lines[k] + '\n'
                    current_line_index += remaining_lines
                
            elif line and not ("..." in line and "existing" in line):
                # This is actual new/edited code
                new_content += lines[i] + '\n'
                current_line_index += 1
            
            i += 1
        
        # Add any remaining original content
        while current_line_index < len(original_lines):
            new_content += original_lines[current_line_index] + '\n'
            current_line_index += 1
        
        
        
        # Write the new content
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content.rstrip('\n') + '\n')
        
        return f"""
Successfully edited file: {target_file}
Instructions applied: {instructions}
Original lines: {len(original_lines)}
New lines: {len(new_content.split('\n'))}
Changes applied successfully!
        """
        
    except FileNotFoundError:
        return f"Error: File '{target_file}' not found"
    except Exception as e:
        return f"Error editing file: {str(e)}"
