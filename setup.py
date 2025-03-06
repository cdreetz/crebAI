from setuptools import setup, find_packages

setup(
    name="llm_inference_server",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.21.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.24.0",
        "requests>=2.28.0",
        # MLX libraries are listed as optional dependencies
    ],
    extras_require={
        "mlx": [
            "mlx>=0.3.0",
            "mlx-lm>=0.0.3",
        ],
        "dev": [
            "pytest>=7.3.1",
            "black>=23.3.0",
            "isort>=5.12.0",
            "mypy>=1.3.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "llm-server=app.main:run",
        ],
    },
    python_requires=">=3.9",
    author="Your Name",
    author_email="youremail@example.com",
    description="FastAPI server for asynchronous LLM inference with MLX on Apple Silicon",
    keywords="llm, fastapi, mlx, inference, api",
    url="https://github.com/yourusername/llm-inference-server",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
