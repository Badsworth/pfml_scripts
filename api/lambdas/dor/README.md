Please refer to the general the shared README at `api/lambdas' for sshared build and release commands.

## Generating Mock files

Generate mock DOR export files

```
make generate
```

Generate with specific number of employers (employees = employer * 15)

```
make generate EMPLOYER_COUNT=2000
```