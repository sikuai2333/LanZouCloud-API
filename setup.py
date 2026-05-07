from pathlib import Path
import re

import setuptools


def read_version():
    init_py = Path(__file__).parent / "lanzou" / "api" / "__init__.py"
    text = init_py.read_text(encoding="utf8")
    match = re.search(r"^version = ['\"]([^'\"]+)['\"]", text, flags=re.M)
    if not match:
        raise RuntimeError("version not found")
    return match.group(1)

with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="lanzou-api",
    version=read_version(),
    author="zaxtyson",
    author_email="zaxtyson@foxmail.com",
    description="LanZouCloud API adapter for login, file management, sharing and transfer workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zaxtyson/LanZouCloud-API",
    project_urls={
        "Source": "https://github.com/zaxtyson/LanZouCloud-API",
        "Issues": "https://github.com/zaxtyson/LanZouCloud-API/issues",
        "Changelog": "https://github.com/zaxtyson/LanZouCloud-API/blob/master/CHANGELOG.md",
    },
    packages=setuptools.find_packages(include=["lanzou", "lanzou.*"]),
    include_package_data=True,
    install_requires=[
        "requests",
        "requests_toolbelt"
    ],
    python_requires=">=3.7",
    keywords=["lanzou", "lanzoucloud", "woozooo", "netdisk", "adapter", "api"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
