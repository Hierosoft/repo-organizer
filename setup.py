from setuptools import setup, find_packages

setup(
    name="repo-organizer",
    version="1.0.0",
    description="Tool to organize and manage GitHub repositories.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Poikilos",
    author_email="7557867+poikilos@users.noreply.github.com",
    url="https://github.com/Hierosoft/repo-organizer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*",
    install_requires=[
        "hierosoft @ git+https://github.com/Hierosoft/hierosoft.git@main",
    ],
    # extras_require={
    #     "dev": [
    #         "pytest",
    #         "flake8",
    #     ],
    # },
    entry_points={
        "console_scripts": [
            "repo-organizer=repoorganizer.__init__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
