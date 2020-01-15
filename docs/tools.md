### Introduction

The root of the monorepo includes tools for code style formatting and linting. Both linting and formatting are enabled in a pre-commit hook set up with [husky](https://www.npmjs.com/package/husky) and [lint-staged](https://github.com/okonet/lint-staged#configuration).

### Linting

This project uses [ESLint](https://eslint.org/) for JavaScript code. To run linting outside of the pre-commit hook:

```
npm run lint
```

### Code Formatting

This project uses [Prettier](https://prettier.io/) for opinionated code formatting.

All .js and .jsx files are automatically re-written using prettier formatting as part of the pre-commit hook.
