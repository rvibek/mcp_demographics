from setuptools import find_packages, setup

setup(
    name="mcp_demographics",
    version="0.1.0",
    description="MCP tool for UNHCR demographics data",
    author="rvibek",
    url="https://github.com/rvibek/mcp_demographics",
    py_modules=["unhcr_demographics"],  # Single module, not a package with subdirs
    install_requires=["requests>=2.28.0", "websocket-client>=1.5.0"],     # Add other dependencies if needed
    entry_points={
        "console_scripts": [
            "unhcr-demographics = unhcr_demographics:main"  
        ]
    }
)