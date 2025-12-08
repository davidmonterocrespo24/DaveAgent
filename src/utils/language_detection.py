"""
Language detection utility based on file extensions.
Migrated from TypeScript implementation.
"""
import os

EXTENSION_TO_LANGUAGE_MAP = {
    '.ts': 'TypeScript',
    '.js': 'JavaScript',
    '.mjs': 'JavaScript',
    '.cjs': 'JavaScript',
    '.jsx': 'JavaScript',
    '.tsx': 'TypeScript',
    '.py': 'Python',
    '.java': 'Java',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.phtml': 'PHP',
    '.cs': 'C#',
    '.cpp': 'C++',
    '.cxx': 'C++',
    '.cc': 'C++',
    '.c': 'C',
    '.h': 'C/C++',
    '.hpp': 'C++',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.rs': 'Rust',
    '.m': 'Objective-C',
    '.mm': 'Objective-C',
    '.pl': 'Perl',
    '.pm': 'Perl',
    '.lua': 'Lua',
    '.r': 'R',
    '.scala': 'Scala',
    '.sc': 'Scala',
    '.sh': 'Shell',
    '.ps1': 'PowerShell',
    '.bat': 'Batch',
    '.cmd': 'Batch',
    '.sql': 'SQL',
    '.html': 'HTML',
    '.htm': 'HTML',
    '.css': 'CSS',
    '.less': 'Less',
    '.sass': 'Sass',
    '.scss': 'Sass',
    '.json': 'JSON',
    '.xml': 'XML',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.md': 'Markdown',
    '.markdown': 'Markdown',
    '.dockerfile': 'Dockerfile',
    '.vim': 'Vim script',
    '.vb': 'Visual Basic',
    '.fs': 'F#',
    '.clj': 'Clojure',
    '.cljs': 'Clojure',
    '.dart': 'Dart',
    '.ex': 'Elixir',
    '.erl': 'Erlang',
    '.hs': 'Haskell',
    '.lisp': 'Lisp',
    '.rkt': 'Racket',
    '.groovy': 'Groovy',
    '.jl': 'Julia',
    '.tex': 'LaTeX',
    '.ino': 'Arduino',
    '.asm': 'Assembly',
    '.s': 'Assembly',
    '.toml': 'TOML',
    '.vue': 'Vue',
    '.svelte': 'Svelte',
    '.gohtml': 'Go Template',
    '.hbs': 'Handlebars',
    '.ejs': 'EJS',
    '.erb': 'ERB',
    '.jsp': 'JSP',
    '.dockerignore': 'Docker',
    '.gitignore': 'Git',
    '.npmignore': 'npm',
    '.editorconfig': 'EditorConfig',
    '.prettierrc': 'Prettier',
    '.eslintrc': 'ESLint',
    '.babelrc': 'Babel',
    '.tsconfig': 'TypeScript',
    '.flow': 'Flow',
    '.graphql': 'GraphQL',
    '.proto': 'Protocol Buffers',
}


def get_language_from_file_path(file_path: str) -> str | None:
    """
    Determines the programming language based on the file extension.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        The name of the language or None if not found.
    """
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension:
        return EXTENSION_TO_LANGUAGE_MAP.get(extension)

    # Check for dotfiles that might be mapped directly (e.g. .gitignore)
    filename = os.path.basename(file_path).lower()
    # In the TS code: return extensionToLanguageMap[`.${filename}`];
    # If filename is ".gitignore", we look up ".gitignore"
    # If filename is "Dockerfile" (no ext), we look up ".Dockerfile" (if mapped)
    # The map has keys like '.dockerfile' and '.gitignore'.

    # If the file starts with '.', os.path.splitext might treat it as extension or filename depending on OS/implementation details usually.
    # But here we handle the case where extension was empty or not found.

    # Try looking up the filename as if it were an extension (prepending dot if needed, but the map keys have dots)
    # The TS code does: extensionToLanguageMap[`.${filename}`]
    # If filename is "Dockerfile", it looks for ".Dockerfile".
    # If filename is ".gitignore", it looks for "..gitignore" which is wrong based on the map keys provided in TS example?
    # Wait, in TS: path.extname('.gitignore') returns '' on some systems or '.gitignore'? 
    # Node path.extname('.index') returns ''
    # Node path.extname('index.html') returns '.html'

    # Let's follow the TS logic:
    # 1. Try extension.
    # 2. If no extension, try `.` + filename.

    # In Python os.path.splitext('.gitignore') returns ('.gitignore', '') on Linux/Mac, but ('.gitignore', '')? 
    # Actually os.path.splitext('.cshrc') -> ('.cshrc', '')
    # So extension is empty.

    # If we have a file named 'Dockerfile', extension is empty.
    # We check map['.dockerfile'].

    # If we have '.gitignore', extension is empty.
    # We check map['..gitignore']? No, the map has '.gitignore'.

    # The TS code says:
    # const filename = path.basename(filePath).toLowerCase();
    # return extensionToLanguageMap[`.${filename}`];

    # If filePath is '.gitignore', filename is '.gitignore'. Key becomes '..gitignore'.
    # But the map has '.gitignore': 'Git'.
    # So the TS code implies that for dotfiles, it expects them to be matched by extension if path.extname returns it, OR by this fallback.
    # But path.extname('.gitignore') is '' in Node.js.
    # So it falls back to `.${filename}` -> `..gitignore`.
    # This suggests the TS code might be slightly buggy for dotfiles unless the map had `..gitignore`.
    # OR, maybe I should just check the filename directly against the map keys if it starts with dot?

    # However, looking at the map:
    # '.dockerfile': 'Dockerfile' -> matches file named 'Dockerfile' via `.` + 'Dockerfile' = '.Dockerfile' (lowercase)
    # '.gitignore': 'Git' -> matches file named '.gitignore' via `.` + '.gitignore' = '..gitignore' ??

    # Let's adjust the python logic to be robust.

    # Case 1: Standard extension
    if extension in EXTENSION_TO_LANGUAGE_MAP:
        return EXTENSION_TO_LANGUAGE_MAP[extension]

    # Case 2: Filename based (e.g. Dockerfile -> .dockerfile)
    filename = os.path.basename(file_path).lower()

    # Try adding a dot (for Dockerfile -> .dockerfile)
    dotted_name = f".{filename}"
    if dotted_name in EXTENSION_TO_LANGUAGE_MAP:
        return EXTENSION_TO_LANGUAGE_MAP[dotted_name]

    # Case 3: The filename itself might be in the map (e.g. .gitignore)
    # The map keys start with dot. If filename is .gitignore, it is in the map.
    if filename in EXTENSION_TO_LANGUAGE_MAP:
        return EXTENSION_TO_LANGUAGE_MAP[filename]

    return None
