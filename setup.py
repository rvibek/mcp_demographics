from setuptools import setup

setup(
    name="unhcr_demographics",
    version="0.1.0",
    scripts=["unhcr_demographics.py"],
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "unhcr-demographics = unhcr_demographics:main"
        ]
    }
)