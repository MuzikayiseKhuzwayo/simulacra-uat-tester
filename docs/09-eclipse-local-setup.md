# 09 — Eclipse Local Setup Guide

This guide explains how to run TestScope AI locally on Windows using Eclipse and PyDev before uploading any code to GitHub.

## 1. Check the prerequisites

You need:

- Python 3.11 or 3.12;
- Eclipse;
- Java 17 or newer for the current PyDev plugin; and
- the extracted TestScope AI project folder.

Open Windows Command Prompt and check Python:

```bat
py --version
```

If Python 3.12 is installed, the result will look similar to:

```text
Python 3.12.x
```

## 2. Check whether PyDev is installed

In Eclipse, open:

```text
Window → Preferences
```

If **PyDev** appears in the left menu, continue to Step 3.

If it does not appear:

1. Select **Help → Install New Software**.
2. Select **Add**.
3. Enter the name `PyDev`.
4. Enter the location `https://www.pydev.org/updates`.
5. Select **PyDev for Eclipse**.
6. Select **Next** and accept the licence if you agree.
7. Complete the installation.
8. Restart Eclipse.

## 3. Extract the project

Extract the supplied ZIP file to a normal development folder, for example:

```text
C:\Users\<your-user-name>\eclipse-workspace\testscope-ai-uat-agent
```

Do not try to open or import the ZIP directly. Eclipse needs the extracted folder.

## 4. Create the virtual environment

Open Command Prompt in the extracted project folder and run:

```bat
py -3.12 -m venv .venv
```

Install the tested dependencies:

```bat
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The `.venv` directory belongs only to your computer and is excluded from Git.

## 5. Configure the interpreter in Eclipse

In Eclipse:

1. Open **Window → Preferences**.
2. Open **PyDev → Interpreters → Python Interpreter**.
3. Select **New**.
4. Enter the name `TestScope AI Python`.
5. Browse to:

   ```text
   <project-folder>\.venv\Scripts\python.exe
   ```

6. Accept the detected Python libraries.
7. Select **Apply and Close**.

Using the project virtual environment ensures Eclipse runs the same Pydantic and Pytest versions recorded in `requirements.txt`.

## 6. Create the Eclipse PyDev project

The extracted sources do not contain Eclipse-specific metadata.

1. Select **File → New → Project**.
2. Select **PyDev → PyDev Project**.
3. Set the project name to `testscope-ai-uat-agent`.
4. Clear **Use default location** if Eclipse displays that option.
5. Select the extracted project folder.
6. Select the Python 3 project type and grammar.
7. Select the `TestScope AI Python` interpreter.
8. Select **Add project directory to the PYTHONPATH**.
9. Select **Finish**.

If Eclipse imported the directory as a general project instead:

1. Right-click the project.
2. Select **PyDev → Set as PyDev Project**.
3. Right-click the project again.
4. Select **PyDev → Set as Source Folder**.

## 7. Run the demonstration

In **PyDev Package Explorer**:

1. Expand `scripts`.
2. Open `demo_schema_validation.py`.
3. Right-click inside the editor.
4. Select **Run As → Python Run**.

The Eclipse Console should show:

```text
1. VALID REQUIREMENT
Result: ACCEPTED by Pydantic

2. INVALID REQUIREMENT — BLANK TITLE
Result: REJECTED by Pydantic

3. INVALID REQUIREMENT — DUPLICATE CRITERION IDs
Result: REJECTED by Pydantic
```

This proves that valid structured input passes and invalid input is blocked.

## 8. Run the automated tests

The most reliable first method is from Command Prompt in the project folder:

```bat
.\.venv\Scripts\python.exe -m pytest -q
```

Expected result:

```text
12 passed
```

You can also right-click the `tests` folder in Eclipse and select the available **Python unit-test** or **Pytest** run option.

## 9. Understand the current execution flow

The current implementation performs:

```text
Requirement data
    → RequirementInput Pydantic model
    → field and business-contract validation
    → accepted structured object or readable validation errors
```

It does not call an AI model yet, and you do not need an OpenAI API key for this demonstration.

## 10. Upload only after local verification

Before uploading to GitHub, confirm:

- the demonstration runs in the Eclipse Console;
- all 12 tests pass;
- `.env` does not exist in the Git staging list;
- `.venv` does not appear in the Git staging list; and
- you understand the validation output.

The next development increment will add `data/sample_requirement.json` and load that file through the same Pydantic contract.
