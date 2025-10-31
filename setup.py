"""
Setup configuration for CodeAgent
"""
from setuptools import setup, find_packages
from pathlib import Path

# Leer el README para la descripción larga
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

setup(
    name="codeagent-cli",
    version="1.0.0",
    author="CodeAgent Team",
    author_email="contact@codeagent.ai",
    description="AI-powered coding assistant with intelligent agent orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/codeagent",
    packages=find_packages(include=['src', 'src.*']),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        # Core dependencies
        "autogen-agentchat>=0.4.0",
        "autogen-ext[openai]>=0.4.0",

        # CLI and UI
        "prompt-toolkit>=3.0.0",
        "rich>=13.0.0",

        # Data processing
        "pandas>=2.0.0",

        # Web tools
        "wikipedia>=1.4.0",

        # Utilities
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'codeagent=src.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai agent coding assistant llm autogen",
)
