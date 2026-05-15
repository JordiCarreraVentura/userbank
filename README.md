

Next steps:
1. Building the package before uploading: 'python -m build' (from "userbank").
2. Upload the package to pypi: 'python -m twine upload --repository {pypi|testpypi} dist/*'
3. Install the package from pypi: 'python -m pip install --index-url {https://test.pypi.org/simple|https://pypi.org/simple} --no-deps userbank'
4. If any dependencies are required, edit the `pyproject.toml` file, "\[project\]" field, and add a `dependencies` key with a `List\[str\]` value, where each string is a `pip`-readable dependency.
