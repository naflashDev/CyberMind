# Tests

This folder contains unit and integration tests for the project.

How to run tests (recommended)

- Use the project's virtual environment Python executable to ensure dependencies are installed and the environment is correct.

- Run all unit tests:

```powershell
C:/Users/nacho/Documents/proyectos_propios/CyberMind/env/Scripts/python.exe -m unittest discover -v
```

- Run only integration tests:

```powershell
C:/Users/nacho/Documents/proyectos_propios/CyberMind/env/Scripts/python.exe -m unittest discover tests/integration -v
```

Installing dependencies for testing

- Recommended: install `dev-requirements.txt` into your virtual environment:

```powershell
C:/Users/nacho/Documents/proyectos_propios/CyberMind/env/Scripts/python.exe -m pip install -r dev-requirements.txt
```

Notes
- Some tests mock heavy dependencies (spaCy, external HTTP services). The `dev-requirements.txt` contains packages required by tests that import modules at import-time.
- CI uses `dev-requirements.txt` to avoid installing the full production `requirements.txt` which may include large model downloads.
