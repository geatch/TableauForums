from setuptools import setup, find_packages

setup(
    name="ForumsScraper",  # Name of the package
    version="0.3.0",  # Package version
    author="Chris Geatch",  # Author's name
    author_email="chris@geatch.com",  # Author's email
    description="For logging the number of points users have on the Tableau Community Forums",  # Short description
    long_description=open("README.md").read(),  # Long description from README
    long_description_content_type="text/markdown",  # Content type of the long description
    url="https://github.com/geatch/TableauForums.git",  # URL to the project's repository
    packages=find_packages(exclude=["credentials"]),  # Automatically discover packages
    classifiers=[
        "Programming Language :: Python :: 3",  # Target Python version
        "License :: OSI Approved :: MIT License",  # License
        "Operating System :: OS Independent",  # OS compatibility
    ],
    python_requires=">=3.10",  # Minimum Python version
    # install_requires=[
    #     "dependency1",
    #     "dependency2",
    #     # Add required dependencies here
    # ],
    # extras_require={
    #     "dev": [
    #         "pytest",
    #         "sphinx",
    #         # Add development dependencies
    #     ],
    # },
    entry_points={
        "console_scripts": [
            "command_name=module_name:main_function",
            # Define CLI commands if any
        ],
    },
)
