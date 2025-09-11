#!/usr/bin/env python3
"""
Apex Decompiler - Setup Script
Superior to Oracle, Medal, and Konstant combined
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = ['numpy>=1.21.0']

setup(
    name="apex-decompiler",
    version="1.0.0",
    description="Superior Luau Bytecode Decompiler - Better than Oracle, Medal & Konstant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Apex Development Team",
    author_email="apex@decompiler.dev",
    url="https://github.com/apex-dev/apex-decompiler",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    install_requires=requirements,
    
    extras_require={
        'gui': ['PyQt6>=6.0.0'],
        'dev': ['pytest>=6.0.0', 'black>=21.0.0', 'flake8>=3.9.0'],
        'docs': ['sphinx>=4.0.0', 'sphinx-rtd-theme>=0.5.0'],
    },
    
    entry_points={
        'console_scripts': [
            'apex-decompiler=apex_decompiler:main',
            'apex-cli=cli.apex_cli:main',
        ],
    },
    
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Disassemblers",
        "Topic :: Security",
    ],
    
    python_requires=">=3.8",
    
    keywords="luau, bytecode, decompiler, reverse-engineering, roblox, anti-obfuscation",
    
    project_urls={
        "Bug Reports": "https://github.com/apex-dev/apex-decompiler/issues",
        "Source": "https://github.com/apex-dev/apex-decompiler",
        "Documentation": "https://apex-decompiler.readthedocs.io/",
    },
)