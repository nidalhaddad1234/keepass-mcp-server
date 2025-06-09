#!/usr/bin/env python3
"""
Setup script for KeePass MCP Server.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="keepass-mcp-server",
    version="1.0.0",
    description="Model Context Protocol server for secure KeePass credential management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="KeePass MCP Server Team",
    author_email="support@keepass-mcp.com",
    url="https://github.com/nidalhaddad1234/keepass-mcp-server",
    license="MIT",
    
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    
    # Dependencies
    install_requires=requirements,
    
    # Entry points
    entry_points={
        "console_scripts": [
            "keepass-mcp-server=keepass_mcp_server.server:main",
        ],
    },
    
    # Package data
    include_package_data=True,
    package_data={
        "keepass_mcp_server": [
            "*.json",
            "*.yml",
            "*.yaml",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration :: Authentication/Directory",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Framework :: AsyncIO",
    ],
    
    # Keywords
    keywords=[
        "keepass",
        "password",
        "credential",
        "mcp",
        "model-context-protocol",
        "security",
        "authentication",
        "automation",
        "browser",
        "ai",
        "claude"
    ],
    
    # Project URLs
    project_urls={
        "Documentation": "https://github.com/nidalhaddad1234/keepass-mcp-server/blob/main/README.md",
        "Source": "https://github.com/nidalhaddad1234/keepass-mcp-server",
        "Tracker": "https://github.com/nidalhaddad1234/keepass-mcp-server/issues",
        "Changelog": "https://github.com/nidalhaddad1234/keepass-mcp-server/blob/main/CHANGELOG.md",
    },
    
    # Additional metadata
    zip_safe=False,
    platforms=["any"],
)
