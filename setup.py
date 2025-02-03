"""Setup file"""
import io

import setuptools

with open("README.md", encoding="utf-8") as fp:
    long_description = fp.read()


def read(*filenames, **kwargs):
    """function to read files like requirements.txt"""
    encoding = kwargs.get("encoding", "utf-8")
    # io.open defaults to \n as universal line ending no matter on what system
    sep = kwargs.get("sep", "\n")
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


def read_requirements(req):
    """function to read requirements"""
    content = read(req)
    requirements = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            continue
        if line.startswith("-r"):
            requirements.extend(read_requirements(line[3:]))
        else:
            requirements.append(line)
    return requirements


setuptools.setup(
    name="resource-schema-guard-rail",
    version="0.0.17",
    description="Schema Guard Rail",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Amazon Web Services",
    author_email="aws-cloudformation-developers@amazon.com",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=["cli"],
    install_requires=read_requirements("requirements.txt"),
    include_package_data=True,
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "guard-rail-cli = cli:main",
            "guard-rail = cli:main",
        ]
    },
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
    ],
)
