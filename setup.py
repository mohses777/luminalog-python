from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="luminalog-sdk",
    version="1.1.0",
    author="LuminaLog Team",
    author_email="support@luminalog.cloud",
    description="LuminaLog SDK - Privacy-first logging with AI-powered debugging",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mohses777/luminalog-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    keywords="logging observability privacy pii debugging luminalog",
    project_urls={
        "Bug Reports": "https://github.com/mohses777/luminalog-python/issues",
        "Source": "https://github.com/mohses777/luminalog-python",
        "Documentation": "https://luminalog.cloud/docs",
    },
)
