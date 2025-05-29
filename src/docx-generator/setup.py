from setuptools import setup, find_packages

setup(
    name="resume-docx-generator",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyyaml>=5.1",
        "python-docx>=0.8.11",
        "jsonschema>=3.2.0",
    ],
    python_requires=">=3.6",
    author="Bruno Bronosky",
    description="Generate Microsoft Word resumes from YAML files following the JSON Resume schema",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "resume-docx=docx_generator.cli:main",
        ],
    },
    package_data={
        "docx_generator": ["templates/*.docx", "schema/*.json"],
    },
) 