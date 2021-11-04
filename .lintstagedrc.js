// .lintstagedrc.js
const path = require("path");

module.exports = {
  "portal/**/*": ["npm run format --prefix=portal -- --write"],
  "!(bin)/**/*.{tf,tfvars}": ["npm run lint:tf"],
  "api/**/*.py": (absolutePaths) => {
    const cwd = process.cwd();
    const RUN_CMD_OPT = (process.env && process.env.RUN_CMD_OPT) || "";
    const isDocker = RUN_CMD_OPT.indexOf("NATIVE") == -1;
    const fileNames = absolutePaths
      .map((filename) => {
        const relativePath = path.relative(cwd, filename);
        if (isDocker) {
          return relativePath.replace("api/", "");
        }
        return filename;
      })
      .join(" ");

    return [`cd ./api && make pre-commit args="${fileNames}"`];
  },
  "api/massgov/pfml/db/**/*": ["npm run-script db-parity-check"],
  "api/openapi.yaml": ["npm run-script spectral"],
};
