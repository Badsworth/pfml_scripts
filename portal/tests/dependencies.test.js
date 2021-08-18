import { join } from "path";
import { testDependencies } from "./lib/jest-dependency-tests";

/** @typedef {import('./lib/jest-dependency-tests').Rule} Rule */

/**
 * Primary configuration defining what modules are not allowed to import what other modules.
 * The configuration consists of an array of rules.
 * @type {Rule[]}
 */
const dependencyRules = [
  {
    // TODO (CP-798): reorganize components into subfolders for "core" reusable components and "pfml"-specific components
    // core components should additionally be forbidden from requiring anything PFML-specific, such as "./src/models"
    // TODO (CP-623): refactor components to remove dependency on next/link, and add "next/link" to forbidden dependencies for all `components`
    moduleOrDirRelPath: "./src/components",
    description:
      "does not depend on framework or PFML-specific application logic",
    forbiddenDependencies: [
      {
        moduleOrDirRelPath: "./src/hooks",
        allowedDependencies: [
          "usePreviousValue",
          "useUniqueId",
          "usePiiHandlers",
          "useFilesLogic",
          "useCollectionState",
          "useThrottledHandler",
          "useAutoFocusEffect",
        ],
        reason:
          "Components should not depend on application code. Consider exposing events that clients handle.",
      },
      {
        moduleOrDirRelPath: "./src/pages",
        reason:
          "Components should not depend on application code. Consider exposing events that clients handle.",
      },
      {
        moduleOrDirRelPath: "next/router",
        reason: "Components should not be responsibile for routing.",
      },
    ],
  },
  {
    moduleOrDirRelPath: "./src/models",
    description: "does not depend on any components or application logic",
    forbiddenDependencies: [
      {
        moduleOrDirRelPath: "js-cookie",
        reason:
          "Models should not have any dependencies. Consider moving state management logic to the app level, or check for accidental dependencies.",
      },
      {
        moduleOrDirRelPath: "next/router",
        reason:
          "Models should not have any dependencies. Consider moving routing logic to the app or page level, or check for accidental dependencies.",
      },
      {
        moduleOrDirRelPath: "./src/components",
        reason:
          "Models should not have any dependencies. Reconsider the software architecture, or check for accidental dependencies.",
      },
      {
        moduleOrDirRelPath: "./src/hooks",
        reason: "",
      },
      {
        moduleOrDirRelPath: "./src/pages",
        reason: "",
      },
    ],
  },
];

describe("dependency tests", () => {
  const rootDir = join(__dirname, "..");
  testDependencies(dependencyRules, rootDir);
});
