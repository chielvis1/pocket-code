from setuptools import setup, find_packages

setup(
    name="pocketcode",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rich>=10.0.0",
        "openai>=1.0.0",
        "pocketflow>=0.1.0",
        "prompt-toolkit>=3.0.0",
        "typer>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "pcode=pocketflow.cli:main",
        ],
    },
    author="Elvis Chi",
    author_email="your.email@example.com",
    description="An AI-powered shell and coding agent",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/chielvis1/pocket-code",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)