from setuptools import setup, find_packages

setup(
    name="yougotmapped",
    version="1.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "folium",
        "python-dotenv",
        "ping3"
    ],
    entry_points={
        "console_scripts": [
            "yougotmapped = yougotmapped.cli:main"
        ]
    },
    author="diputs",
    author_email="diputs-sudo@proton.me",
    description="A terminal tool to map IPs and domains with style.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/diputs-sudo/YouGotMapped",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
