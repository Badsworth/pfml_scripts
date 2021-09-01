import { basename, extname, join } from "path";
import { readdirSync, statSync } from "fs";

/**
 * An object describing a forbidden dependency and the reason why it's forbidden.
 * @typedef {object} ForbiddenDependency
 * @property {string} moduleOrDirRelPath Relative path to the module or directory of modules
 * @property {string[]} allowedDependencies Skip forbidding of these module file names
 * @property {string} reason Reason why this dependency is forbidden. This reason will show up in the test's error message if this dependency is imported.
 */

/**
 * A configuration for a single rule defining what module(s) are not allowed to import
 * what other modules. A rule consists of the relative path to a module or folder of modules,
 * an array of forbidden dependencies (each of which can be a single module or folder of modules),
 * and a description of the rule for use in jest unit test descriptions.
 * @typedef {object} Rule
 * @property {string} moduleOrDirRelPath Relative path to the module or directory of modules
 * @property {string} description Description of rule
 * @property {ForbiddenDependency[]} forbiddenDependencies Array of forbidden dependencies. Each element can be the relative path to a single module or a directory of modules
 */

/**
 * Given a set of rules specifying what modules are not allowed to import what other modules,
 * this function generates a set of tests.
 *
 * For each rule, this function generates a test suite using
 * the jest `describe` function. The description of the suite is "[module] dependencies".
 *
 * Within each test suite, for each forbidden dependency, this function generates a unit test using
 * the jest `it` function. The description of the test is configured by the rule.description.
 *
 * For each unit test, all the forbidden dependencies are mocked out and replaced with a function that throws
 * an error, and then the module(s) being tested is `require`'d. When requiring the module, if any of the
 * forbidden dependencies are imported, the error will be thrown, causing the test to fail. The error message
 * will include the name of the forbidden dependency, and why it should not be included.
 *
 * @param {Rule[]} dependencyRules Array of dependency rules describing what modules are not allowed to import what other modules
 * @param {string} rootDir The root directory to which paths are relative
 */
// eslint-disable-next-line jest/no-export
export const testDependencies = (dependencyRules, rootDir) => {
  beforeEach(() => {
    jest.resetModules();
  });

  // Define a test suite for each of the rules
  for (const {
    forbiddenDependencies,
    moduleOrDirRelPath,
    description,
  } of dependencyRules) {
    const moduleOrDirName = basename(moduleOrDirRelPath, ".js");
    describe(`${moduleOrDirName} dependencies`, () => {
      beforeEach(() => {
        mockForbiddenDependenciesToThrow(forbiddenDependencies, rootDir);
      });

      for (const modulePath of getModulePaths(moduleOrDirRelPath, rootDir)) {
        const moduleName = basename(modulePath, ".js");
        it(`${moduleName} ${description}`, () => {
          const importModule = () => require(modulePath);
          expect(importModule).not.toThrow();
        });
      }
    });
  }
};

/**
 * Takes a relative path to a module or a folder and returns an array of module paths.
 * If the path is to a single module, then returns an array containing a path to that one module.
 * If the path is to a folder of modules, then returns an array containing all modules within that folder (recursively).
 * If the module path is a node module, just returns an array with one string containing that node module name.
 * @param {string} moduleOrDirRelPath Relative path to module or folder of modules
 * @param {string} rootDir The root directory to which paths are relative
 * @returns {string[]} Array of paths to modules
 */
function getModulePaths(moduleOrDirRelPath, rootDir) {
  // if module doesn't start with "." or ".." then it's a node module
  if (!moduleOrDirRelPath.startsWith(".")) {
    const nodeModule = moduleOrDirRelPath;
    return [nodeModule];
  }
  const moduleOrDirPath = join(rootDir, moduleOrDirRelPath);
  if (statSync(moduleOrDirPath).isDirectory()) {
    const dirPath = moduleOrDirPath;
    const modulePaths = listFilesRecursive(dirPath);
    // only return js modules (ignore files like .eslintrc)
    return modulePaths.filter((modulePath) => extname(modulePath) === ".js");
  } else {
    const modulePath = moduleOrDirPath;
    return [modulePath];
  }
}

/**
 * Given a list of dependencies, mocks each dependency with a module that throws an error, effectively
 * preventing that module from being imported. The error includes the name of the module that was included.
 * Each forbidden dependency can be a single module or a folder of modules.
 * @param {string[]} forbiddenDependencies Array of forbidden dependencies. Each element can be a single module or a folder of modules.
 * @param {string} rootDir The root directory to which paths are relative
 */
function mockForbiddenDependenciesToThrow(forbiddenDependencies, rootDir) {
  for (const {
    moduleOrDirRelPath,
    reason,
    allowedDependencies,
  } of forbiddenDependencies) {
    for (const modulePath of getModulePaths(moduleOrDirRelPath, rootDir)) {
      if (allowedDependencies) {
        const allowModule = allowedDependencies.some(
          (filename) => !!modulePath.match(filename)
        );
        if (allowModule) continue;
      }

      jest.doMock(modulePath, () => {
        throw new Error(`${modulePath} is a forbidden dependency. ${reason}`);
      });
    }
  }
}

/**
 * Lists all files within a directory, recursively traversing subdirectories.
 * Returns an array of file paths, not including the subdirectories themselves.
 * @param {string} dir Path to directory
 * @returns {string[]} Array of file paths
 */
function listFilesRecursive(dir) {
  const files = [];

  // Starting from `dir` as the root directory, iterate over directory tree
  // in a breadth-first fashion and adding the full path of all files to the
  // list of `files`
  const queueOfDirsToTraverse = [dir];
  while (queueOfDirsToTraverse.length > 0) {
    const currentDir = queueOfDirsToTraverse.shift();
    // Iterate through the items in the directory
    // If the item is a subdirectory, then add it to the list of directories to traverse
    // otherwise it's file, so add it to our list of files
    const children = readdirSync(currentDir);
    for (const child of children) {
      const childPath = join(currentDir, child); // construct full path
      if (statSync(childPath).isDirectory()) {
        queueOfDirsToTraverse.push(childPath);
      } else {
        files.push(childPath);
      }
    }
  }
  return files;
}

// eslint-disable-next-line jest/no-export
export default { testDependencies };
