"""Fix poetry 1.7.0 packaging issues. Stub out empty module
- The current project could not be installed: [Errno 3] No such file or directory:
- The current project could not be installed: No file/folder found for package
- https://github.com/python-poetry/poetry/issues/1132
- https://github.com/python-poetry/poetry/issues/1537
- https://github.com/python-poetry/poetry/issues/2458
- https://discuss.python.org/t/projects-that-arent-meant-to-generate-a-wheel-and-pyproject-toml/29684
 """
