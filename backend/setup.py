"""Setup for older pip versions that don't support pyproject.toml editable install."""
from setuptools import setup, find_packages

setup(
    name="bullbeararena",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn>=0.34.0",
        "httpx>=0.28.0",
        "litellm>=1.60.0",
        "pydantic>=2.10.0",
        "typer>=0.15.0",
        "rich>=13.9.0",
        "yfinance>=0.2.50",
    ],
)
