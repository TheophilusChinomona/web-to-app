from setuptools import find_namespace_packages, setup

setup(
    name="cli-anything-web-to-app",
    version="0.1.0",
    description="CLI-Anything harness for the web-to-app repository",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    include_package_data=True,
    install_requires=["click>=8.1.0"],
    entry_points={
        "console_scripts": [
            "cli-anything-web-to-app=cli_anything.web_to_app.__main__:main",
        ]
    },
    python_requires=">=3.9",
)
