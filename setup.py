from setuptools import setup

setup(
    url="https://github.com/henryivesjones/slack-slash",
    packages=["slash_slack"],
    package_dir={"slash_slack": "slash_slack"},
    package_data={"slash_slack": ["py.typed"]},
    include_package_data=True,
)
