"""
Setup script for Greenhouse Heating System
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="greenhouse-heating-system",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="TRACE-MODE compatible greenhouse heating system emulator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/greenhouse-heating",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "greenhouse-sim=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.toml", "*.md"],
    },
)
