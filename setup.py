"""Setup script for the reels generator package."""

from setuptools import setup, find_packages

setup(
    name="reels_gen",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "Pillow>=10.0.0",
        "moviepy>=1.0.3",
    ],
    entry_points={
        "console_scripts": [
            "reels-gen=src.core.dialogue_generator:main",
        ],
    },
    author="Oceanvisual",
    author_email="your.email@example.com",
    description="Генератор коротких видео с диалогами в стиле Rick and Morty",
    long_description=open("docs/README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Oceanvisual/HAOreelsGEN",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
) 