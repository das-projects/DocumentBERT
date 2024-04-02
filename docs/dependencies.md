# Dependencies

To ensure consistent und reproducible Python environments, we use [`pip-tools`](https://pip-tools.readthedocs.io/en/latest/) to create requirements files that contain only pinned versions of all dependencies and transient dependencies.
To manage different sets of dependencies for each context, for example, training or processing, all dependencies are added as "optional dependencies" to the `pyproject.toml`.
We use `pip-compile` to first create a `requirements.txt`, which includes all optional dependencies.
This ensures, that all selected versions are compatible with each other and can be installed in the same virtual Python environment.
We then compile different subsets by selecting different sets of optional dependencies, but constraining them to the compiled development dependencies.

## Common Workflows

### New Dependency

> I need a new dependency

Add the dependency to the appropriate optional dependencies in `pyproject.toml` and run `task setup:update-dependencies`.

### Upgrade a single Dependency

> I want to upgrade a dependency to its latest version

Run `task setup:update-dependencies -- -P <dependency name>`.
Anything after the `--` in the task command will be forwarded to the compilation of the development dependencies to which all other subsets of dependencies are constrained.

### Constrain the Version of a single Dependency

> I want to constrain a dependency to a specific minimum version to avoid a security issue

If not already, add the dependency in question to the appropriate optional dependency and specify a lower bound on the version to exclude affected versions, e.g., `pandas>1.3`, and run `task setup:update-dependencies`.

### Upgrade all Dependencies

> I want to update all dependencies to their latest versions

Run `task setup:update-dependencies -- -U`.

### Create a new Subset of Dependencies

> I need a new subset of dependencies to build a task-specific Docker image

Go to the file `tasks/setup.yaml` and look at the task `update-dependencies`.
Add a new line below the lines starting with `{{.SUBSET_COMPILE_COMMAND}}` and configure the `--extra` flag to include all optional groups you need in this subset of dependencies and set the `-o` flag to point to where you want your new requirements file to exist.
Save the task file and run `task setup:update-dependencies`.
