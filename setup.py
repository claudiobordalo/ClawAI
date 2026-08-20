from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="clawaii",
    version="0.1.0",
    author="Claw AI Team",
    author_email="contact@clawai.dev",
    description="Cognitive architecture for Claw AI including memory, learning and planning systems.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/claw-ai/clawaii",  
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)