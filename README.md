# python-batchtools

## Set up your development environment

### Install tools

1. Start by installing `uv`. Depending on your distribution, this may be as simple as:

    ```sh
    sudo dnf -y install uv
    ```

    If you would like to run the latest version, you can install the command using `pipx`. First, install `pipx`:

    ```
    sudo dnf -y install pipx
    ```

    And then use `pipx` to install `uv`:

    ```
    pipx install uv
    ```

2. Next, install `pre-commit`. As with `uv`, you can install this using your system package manager:

    ```
    sudo dnf -y install pre-commit
    ```

    Or you can install a possibly more recent version using `pipx`:

    ```
    pipx install pre-commit
    ```


### Activate pre-commit

Activate `pre-commit` for your working copy of this repository by running:

```
pre-commit install
```

This will configure `.git/hooks/pre-commit` to run the `pre-commit` tool every time you make a commit. Running these tests locally ensures that your code is clean and that tests are passing before you share your code with others. To manually run all the checks:

```
pre-commit run --all-files
```


### Install dependencies

To install the project dependencies, run:

```
uv sync --all-extras
```

### Run tests

To run just the unit tests:

```
uv run pytest
```

This will generate a test coverage report in `htmlcov/index.html`.
