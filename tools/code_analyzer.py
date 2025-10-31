#!/usr/bin/env python3
"""
Function-based code analysis capabilities for MCP File Editor
"""

import ast
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

class CodeAnalyzer:
    """Analyzes code files to extract function and structure information"""
    
    @staticmethod
    def parse_python_file(content: str) -> ast.AST:
        """Parse Python code and return AST"""
        try:
            return ast.parse(content)
        except SyntaxError as e:
            raise ValueError(f"Python syntax error: {e}")
    
    @staticmethod
    def get_docstring(node: ast.AST) -> Optional[str]:
        """Extract docstring from an AST node"""
        docstring = ast.get_docstring(node)
        return docstring.strip() if docstring else None
    
    @staticmethod
    def get_function_signature(node: ast.FunctionDef) -> str:
        """Get function signature as a string"""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        
        # Add defaults
        defaults_start = len(args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            args[defaults_start + i] += "=..."
            
        # Add *args and **kwargs
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
            
        return f"{node.name}({', '.join(args)})"
    
    @staticmethod
    def extract_functions_from_python(content: str) -> List[Dict[str, Any]]:
        """Extract all functions from Python code"""
        tree = CodeAnalyzer.parse_python_file(content)
        functions = []
        
        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self, source_lines):
                self.functions = []
                self.source_lines = source_lines
                self.current_class = None
                
            def visit_ClassDef(self, node):
                old_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = old_class
                
            def visit_FunctionDef(self, node):
                func_info = {
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno,
                    "signature": CodeAnalyzer.get_function_signature(node),
                    "docstring": CodeAnalyzer.get_docstring(node),
                    "decorators": [d.id if isinstance(d, ast.Name) else ast.unparse(d) 
                                  for d in node.decorator_list],
                    "is_method": self.current_class is not None,
                    "class_name": self.current_class,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                }
                
                # Get return type if annotated
                if node.returns:
                    func_info["return_type"] = ast.unparse(node.returns)
                    
                # Get parameter types if annotated
                param_types = {}
                for arg in node.args.args:
                    if arg.annotation:
                        param_types[arg.arg] = ast.unparse(arg.annotation)
                if param_types:
                    func_info["param_types"] = param_types
                    
                self.functions.append(func_info)
                self.generic_visit(node)
        
        visitor = FunctionVisitor(content.splitlines())
        visitor.visit(tree)
        return visitor.functions
    
    @staticmethod
    def extract_functions_from_javascript(content: str) -> List[Dict[str, Any]]:
        """Extract functions from JavaScript/TypeScript code using regex"""
        functions = []
        
        # Regex patterns for different function styles
        patterns = [
            # Regular function declaration
            r'(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
            # Arrow function assigned to const/let/var
            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*(?::\s*[^=]+)?\s*=>',
            # Method in class
            r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
        ]
        
        lines = content.splitlines()
        for i, line in enumerate(lines):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    # Simple heuristic to find end of function
                    brace_count = 0
                    start_line = i + 1
                    end_line = start_line
                    
                    for j in range(i, len(lines)):
                        brace_count += lines[j].count('{') - lines[j].count('}')
                        if brace_count == 0 and j > i:
                            end_line = j + 1
                            break
                    
                    functions.append({
                        "name": func_name,
                        "line_start": start_line,
                        "line_end": end_line,
                        "signature": line.strip(),
                        "is_async": 'async' in line
                    })
                    break
        
        return functions
    
    @staticmethod
    def find_function_at_line(functions: List[Dict[str, Any]], line_number: int) -> Optional[Dict[str, Any]]:
        """Find which function contains a given line number"""
        for func in functions:
            if func["line_start"] <= line_number <= func["line_end"]:
                return func
        return None
    
    @staticmethod
    def extract_imports_from_python(content: str) -> List[Dict[str, Any]]:
        """Extract import statements from Python code"""
        tree = CodeAnalyzer.parse_python_file(content)
        imports = []
        
        class ImportVisitor(ast.NodeVisitor):
            def __init__(self):
                self.imports = []
                
            def visit_Import(self, node):
                for alias in node.names:
                    self.imports.append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno
                    })
                    
            def visit_ImportFrom(self, node):
                module = node.module or ""
                for alias in node.names:
                    self.imports.append({
                        "type": "from",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno
                    })
        
        visitor = ImportVisitor()
        visitor.visit(tree)
        return visitor.imports
    
    @staticmethod
    def extract_classes_from_python(content: str) -> List[Dict[str, Any]]:
        """Extract class definitions from Python code"""
        tree = CodeAnalyzer.parse_python_file(content)
        classes = []
        
        class ClassVisitor(ast.NodeVisitor):
            def __init__(self):
                self.classes = []
                
            def visit_ClassDef(self, node):
                class_info = {
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno,
                    "docstring": CodeAnalyzer.get_docstring(node),
                    "bases": [ast.unparse(base) for base in node.bases],
                    "decorators": [d.id if isinstance(d, ast.Name) else ast.unparse(d) 
                                  for d in node.decorator_list],
                    "methods": []
                }
                
                # Get methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        class_info["methods"].append({
                            "name": item.name,
                            "line": item.lineno,
                            "is_async": isinstance(item, ast.AsyncFunctionDef)
                        })
                
                self.classes.append(class_info)
                self.generic_visit(node)
        
        visitor = ClassVisitor()
        visitor.visit(tree)
        return visitor.classes


# Tool implementations for MCP

async def list_functions(
    path: str,
    language: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all functions in a code file.
    
    Args:
        path: File path
        language: Programming language (auto-detected if not specified)
        
    Returns:
        List of function information including name, line numbers, signature, etc.
    """
    from server import resolve_path, is_safe_path, get_file_type
    
    file_path = resolve_path(path)
    if not is_safe_path(file_path):
        raise ValueError("Invalid path: directory traversal detected")
    
    if not file_path.exists():
        raise ValueError(f"File does not exist: {path}")
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Auto-detect language if not specified
    if not language:
        suffix = file_path.suffix.lower()
        if suffix in ['.py', '.pyw']:
            language = 'python'
        elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
            language = 'javascript'
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    # Extract functions based on language
    if language == 'python':
        return CodeAnalyzer.extract_functions_from_python(content)
    elif language in ['javascript', 'typescript']:
        return CodeAnalyzer.extract_functions_from_javascript(content)
    else:
        raise ValueError(f"Unsupported language: {language}")


async def get_function_at_line(
    path: str,
    line_number: int,
    language: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get the function that contains a specific line number.
    
    Args:
        path: File path
        line_number: Line number to search for
        language: Programming language (auto-detected if not specified)
        
    Returns:
        Function information if found, None otherwise
    """
    functions = await list_functions(path, language)
    return CodeAnalyzer.find_function_at_line(functions, line_number)


async def get_code_structure(
    path: str,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the overall code structure of a file.
    
    Args:
        path: File path
        language: Programming language (auto-detected if not specified)
        
    Returns:
        Dictionary containing imports, classes, functions, and other structural elements
    """
    from server import resolve_path, is_safe_path
    
    file_path = resolve_path(path)
    if not is_safe_path(file_path):
        raise ValueError("Invalid path: directory traversal detected")
    
    if not file_path.exists():
        raise ValueError(f"File does not exist: {path}")
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Auto-detect language if not specified
    if not language:
        suffix = file_path.suffix.lower()
        if suffix in ['.py', '.pyw']:
            language = 'python'
        elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
            language = 'javascript'
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    structure = {
        "language": language,
        "file": str(file_path.name),
        "lines": len(content.splitlines())
    }
    
    if language == 'python':
        structure["imports"] = CodeAnalyzer.extract_imports_from_python(content)
        structure["classes"] = CodeAnalyzer.extract_classes_from_python(content)
        structure["functions"] = CodeAnalyzer.extract_functions_from_python(content)
    elif language in ['javascript', 'typescript']:
        structure["functions"] = CodeAnalyzer.extract_functions_from_javascript(content)
        # TODO: Add JS/TS import and class extraction
    
    return structure


async def search_functions(
    pattern: str,
    path: str = ".",
    file_pattern: str = "*.py",
    recursive: bool = True,
    max_depth: Optional[int] = None
) -> Dict[str, Any]:
    """
    Search for functions by name pattern across files.
    
    Args:
        pattern: Function name pattern (regex)
        path: Directory to search in
        file_pattern: File name pattern
        recursive: Search recursively
        max_depth: Maximum depth for recursive search
        
    Returns:
        Dictionary with search results
    """
    from server import resolve_path, is_safe_path, walk_with_depth
    import re
    
    search_path = resolve_path(path)
    if not is_safe_path(search_path):
        raise ValueError("Invalid path: directory traversal detected")
    
    regex = re.compile(pattern)
    results = []
    files_searched = 0
    
    # Get files to search
    if search_path.is_file():
        files_to_search = [search_path]
    else:
        if recursive:
            if max_depth is not None:
                files_to_search = list(walk_with_depth(search_path, file_pattern, max_depth))
            else:
                files_to_search = list(search_path.rglob(file_pattern))
        else:
            files_to_search = list(search_path.glob(file_pattern))
    
    for file_path in files_to_search:
        if not file_path.is_file():
            continue
        
        try:
            # Get language from file extension
            suffix = file_path.suffix.lower()
            if suffix in ['.py', '.pyw']:
                language = 'python'
            elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
                language = 'javascript'
            else:
                continue
            
            # Get functions from file
            functions = await list_functions(str(file_path.relative_to(search_path)), language)
            files_searched += 1
            
            # Search function names
            matching_functions = []
            for func in functions:
                if regex.search(func["name"]):
                    matching_functions.append(func)
            
            if matching_functions:
                results.append({
                    "file": str(file_path.relative_to(search_path)),
                    "functions": matching_functions
                })
                
        except Exception:
            continue
    
    return {
        "results": results,
        "files_searched": files_searched,
        "total_functions": sum(len(r["functions"]) for r in results)
    }