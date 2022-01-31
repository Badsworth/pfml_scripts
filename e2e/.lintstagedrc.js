// This configuration is a little strange - because it's a subdirectory configuration,
// we ran into issues with relative paths. Eg: `eslint` would refer to the eslint from
// your current working directory rather than this directory.
// To work around this, we've explicitly changed directories into this directory for
// each step, and used npx to reference the binary name.
// This can be cleaned up once this PR gets in:
// https://github.com/okonet/lint-staged/pull/1091
const root = __dirname;
module.exports = {
  "*.{js,ts}": [
    `cd ${root} && npx eslint --cache --fix`,
    `cd ${root} && npx prettier --write`,
  ],
  // It's not possible to typecheck one file at a time, so we use a function
  // here to typecheck the whole directory. Slow, but guaranteed to work.
  "*.ts": () => [`cd ${root} && npx tsc --noEmit`],
  "*.{css,md,yml,json}": `cd ${root} && npx prettier --write`,
};
