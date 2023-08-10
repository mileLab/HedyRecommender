SET KICAD_PYTHON_EXEC=C:\Program Files\KiCad\6.0\bin\python.exe
coverage run --source source -m pytest -v "source\tests" && coverage report -m
coverage html && start "" "htmlcov/index.html"