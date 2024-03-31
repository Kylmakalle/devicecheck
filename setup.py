import codecs
import os.path

import setuptools

with open("Readme.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setuptools.setup(
    name="devicecheck",
    version=get_version("devicecheck/__init__.py"),
    author="Sergey Akentev",
    author_email='"S. Akentev" <sergey+gh@akentev.com>',
    description="Apple DeviceCheck API. Reduce fraudulent use of your services by managing device state and asserting app integrity.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Kylmakalle/devicecheck",
    project_urls={
        "Issue Tracker": "https://github.com/Kylmakalle/devicecheck/issues",
        "Repository": "https://github.com/Kylmakalle/devicecheck",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests>=2.20.0",
        "pyjwt>=2.8.0",
        "cryptography>=3.4.7"
    ],
    extras_require={
        'async': ['aiohttp>=3.8']
    },
    packages=["devicecheck"],
    python_requires=">=3.6",
)
