The `justfile` provides development commands that can be run.
Use `just` to list the available recipes.

For example, to run python snippets, use `just shell`:

```{bash}
echo 'print("Hello world!")' | just shell
```

This will ensure that the right environment is used and django is configured with development settings.


## Wagtail Specifics

- This project is currently not intended to be used with private pages. Pages that are published are assumed to be public.
- This project is currently not intended to be used as a multisite project.