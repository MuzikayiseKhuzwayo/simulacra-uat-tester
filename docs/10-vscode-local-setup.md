# 10 — VS Code Local Setup Guide

This guide explains how to open, run and test TestScope AI locally on Windows using Visual Studio Code before uploading the project to GitHub.

## 1. Open the complete project folder

Extract the supplied ZIP file. In VS Code, select:

```text
File → Open Folder
```

Select the extracted `testscope-ai-uat-agent` folder, not the individual `schemas.py` file.

The Explorer should show folders including:

```text
docs
scripts
src
tests
```

## 2. Install the Microsoft Python extension

1. Select the **Extensions** icon in the left activity bar.
2. Search for `Python`.
3. Install **Python**, published by **Microsoft**.
4. Reload VS Code if requested.

The extension provides interpreter selection, Python execution, IntelliSense and test discovery.

## 3. Check Python

Open:

```text
Terminal → New Terminal
```

Run:

```powershell
py --version
```

Python 3.11 or 3.12 is recommended. The expected response looks similar to:

```text
Python 3.12.x
```

## 4. Create the project environment

From the VS Code terminal, ensure the current path is the project root—the folder containing `requirements.txt`.

Run:

```powershell
py -3.12 -m venv .venv
```

Install the dependencies without requiring PowerShell activation:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

This installs Pydantic, python-dotenv and Pytest only inside this project.

## 5. Select the correct interpreter

1. Press **Ctrl+Shift+P**.
2. Search for `Python: Select Interpreter`.
3. Select the interpreter containing:

   ```text
   .venv\Scripts\python.exe
   ```

4. If it is not listed, select **Enter interpreter path** and browse to that file.

The selected interpreter should appear in the VS Code status bar. The yellow underline below `pydantic` should disappear after the Python language service refreshes.

If it remains:

1. Press **Ctrl+Shift+P**.
2. Run `Developer: Reload Window`.
3. Confirm that `.venv` is still the selected interpreter.

## 6. Run the schema demonstration

Open:

```text
scripts/demo_schema_validation.py
```

Use either method:

- select the **Run Python File** play button in the top-right corner; or
- right-click the editor and select **Run Python File in Terminal**.

Expected output:

```text
1. VALID REQUIREMENT
Result: ACCEPTED by Pydantic

2. INVALID REQUIREMENT — BLANK TITLE
Result: REJECTED by Pydantic

3. INVALID REQUIREMENT — DUPLICATE CRITERION IDs
Result: REJECTED by Pydantic
```

## 7. Run all automated tests

In the VS Code terminal, run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected result:

```text
12 passed
```

You can also use VS Code's Testing view:

1. Select the **Testing** beaker icon.
2. If prompted, select **Configure Python Tests**.
3. Select **pytest**.
4. Select the repository root.
5. Use the play button to run all discovered tests.

## 8. What is currently working?

The current flow is:

```text
Requirement data
    → Pydantic RequirementInput model
    → required-field and traceability validation
    → accepted object or readable errors
```

No AI model is called yet, and no OpenAI API key is required for this stage.

## 9. Keep local files out of GitHub

The following must not be uploaded:

```text
.venv
.env
__pycache__
.pytest_cache
```

They are already listed in `.gitignore`.

Upload to GitHub only after:

- the demonstration runs;
- all 12 tests pass;
- Pydantic no longer has an unresolved-import warning; and
- the project is opened as a folder in VS Code.
