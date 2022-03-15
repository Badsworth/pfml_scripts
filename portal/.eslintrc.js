const path = require("path");

module.exports = {
  root: true,
  globals: {
    // Trackers loaded globally
    newrelic: "readonly",
    globalThis: "readonly",
  },
  env: {
    browser: true,
    es6: true,
    node: true,
    jest: true,
  },
  extends: [
    "nava",
    "plugin:jest/recommended",
    "plugin:jsdoc/recommended",
    "prettier",
    "plugin:jsx-a11y/recommended",
    "plugin:react/recommended",
    "plugin:you-dont-need-lodash-underscore/all",
  ],
  plugins: ["jest", "jsdoc", "lodash", "todo-plz", "jsx-a11y", "react-hooks"],
  parser: "@babel/eslint-parser",
  parserOptions: {
    ecmaVersion: 2018,
    sourceType: "module",
    ecmaFeatures: {
      jsx: true,
    },
  },
  overrides: [
    {
      files: "**/*.+(ts|tsx)",
      parser: "@typescript-eslint/parser",
      parserOptions: {
        project: path.resolve(__dirname, "./tsconfig.json"),
        tsconfigRootDir: path.resolve(__dirname),
      },
      plugins: ["@typescript-eslint/eslint-plugin"],
      extends: [
        "plugin:@typescript-eslint/eslint-recommended", // removes redundant warnings between TS & ESLint
        "plugin:@typescript-eslint/recommended", // rules specific to typescript, e.g., writing interfaces
      ],
      rules: {
        "@typescript-eslint/ban-ts-comment": [
          "error",
          {
            // Allow disabling type checking on a file as long as there's an
            // accompanying description for why it's disabled:
            "ts-nocheck": "allow-with-description",
          },
        ],
        // conflicts with @typescript-eslint/no-use-before-define:
        "no-use-before-define": "off",
        "@typescript-eslint/consistent-indexed-object-style": [
          "error",
          // Index signature allows us to be more expressive than Record.
          // For example { [claim_id: string]: Claim }, compared to Record<string, Claim>
          "index-signature",
        ],
        // suppress noisy errors that didn't exist prior to TS migration:
        "@typescript-eslint/no-use-before-define": "off",
        "@typescript-eslint/array-type": ["error", { default: "array-simple" }],
        "@typescript-eslint/consistent-type-definitions": "error",
        "@typescript-eslint/explicit-module-boundary-types": "off",
        "@typescript-eslint/naming-convention": [
          "error",
          {
            selector: "typeLike",
            format: ["PascalCase"],
          },
        ],
        "@typescript-eslint/no-parameter-properties": "error",
        "@typescript-eslint/no-unused-vars": [
          "error",
          { argsIgnorePattern: "^_", ignoreRestSiblings: true },
        ],
        // conflicts with @typescript-eslint/strict-boolean-expressions:
        "no-extra-boolean-cast": "off",
        "@typescript-eslint/strict-boolean-expressions": [
          "error",
          {
            // These are pretty lax as a starting point, but helps
            // catch unneeded boolean expressions, or nullable numbers
            // that are accidentally treated as booleans:
            allowAny: true,
            allowNullableBoolean: true,
            allowNullableString: true,
          },
        ],
        "jsdoc/check-param-names": "off",
        "jsdoc/require-param-type": "off",
        "jsdoc/require-property-type": "off",
        "jsdoc/require-returns": "off",
        "jsdoc/require-returns-type": "off",
        "no-restricted-syntax": [
          "error",
          {
            selector: "TSEnumDeclaration",
            message:
              "Don't use TypeScript enum syntax. Use `as const` instead.",
          },
        ],
      },
    },
    {
      files: ["src/components/*"],
      rules: {
        "no-restricted-imports": [
          "error",
          {
            paths: [
              {
                name: "next/router",
                message: "Components should not be responsibile for routing.",
              },
            ],
            patterns: [
              {
                group: ["*/pages*"],
                message:
                  "Components should not depend on application code. Consider exposing events that clients handle.",
              },
            ],
          },
        ],
      },
    },
    {
      files: ["src/components/core/*"],
      rules: {
        "no-restricted-imports": [
          "error",
          {
            paths: [
              {
                name: "react-i18next",
                message: "Core components shouldn't have any custom strings",
              },
              {
                name: "next/link",
                message:
                  "Core components should not be responsible for routing.",
              },
            ],
            patterns: [
              {
                group: [
                  "*/pages*",
                  "*/components*.tsx",
                  "*/models*",
                  "*/locales/*",
                  "*/flows*",
                  "*/hoc*",
                  "*/services*",
                ],
                message:
                  "Core components should not depend on application code.",
              },
            ],
          },
        ],
      },
    },
    {
      files: ["src/models/*"],
      rules: {
        "no-restricted-imports": [
          "error",
          {
            paths: [
              {
                name: "next/router",
                message:
                  "Models should not have any dependencies. Consider moving routing logic to the app or page level, or check for accidental dependencies.",
              },
              {
                name: "js-cookie",
                message:
                  "Models should not have any dependencies. Consider moving routing logic to the app or page level, or check for accidental dependencies.",
              },
            ],
            patterns: [
              {
                group: ["*/components*"],
                message:
                  "Models should not have any dependencies. Reconsider the software architecture, or check for accidental dependencies.",
              },
              {
                group: ["*/pages*"],
                message:
                  "Models should not have any dependencies. Reconsider the software architecture, or check for accidental dependencies.",
              },
              {
                group: ["*/hooks*"],
                message:
                  "Models should not have any dependencies. Reconsider the software architecture, or check for accidental dependencies.",
              },
            ],
          },
        ],
      },
    },
    {
      files: ["lib/**", "src/**", "storybook/**"],
      rules: {
        "no-restricted-imports": [
          "error",
          {
            patterns: [
              {
                group: ["**/tests/*"],
                message:
                  "Test files should not be imported in files outside of the tests/ directory. Code shared between Storybook and Tests should be in the lib/ directory.",
              },
            ],
          },
        ],
      },
    },
  ],
  rules: {
    camelcase: "off",
    "import/no-useless-path-segments": "error",
    "jest/consistent-test-it": ["error", { fn: "it" }],
    "jest/no-conditional-expect": "off",
    "jest/no-try-expect": "off",
    "jest/valid-title": "off",
    "jsdoc/check-param-names": "error",
    "jsdoc/newline-after-description": "off",
    "jsdoc/require-jsdoc": "off",
    "jsdoc/require-param": "off",
    "jsdoc/require-param-description": "off",
    "jsdoc/require-param-name": "error",
    "jsdoc/require-param-type": "error",
    "jsdoc/require-returns": "warn",
    "jsdoc/require-returns-description": "off",
    "jsdoc/no-undefined-types": "off",
    "jsdoc/tag-lines": "off",
    "jsx-a11y/anchor-has-content": "off",
    "jsx-a11y/no-onchange": "off",
    "lodash/import-scope": ["error", "member"],
    "lodash/path-style": ["error", "string"],
    "no-console": ["error", { allow: ["error"] }],
    "no-irregular-whitespace": ["error", { skipTemplates: true }],
    "no-param-reassign": "error",
    "no-prototype-builtins": "off",
    "object-shorthand": ["error", "properties", { avoidQuotes: true }],
    "promise/no-native": "off",
    "react/button-has-type": "error",
    "react/jsx-handler-names": "off",
    "react/jsx-fragments": ["error", "element"],
    "react/jsx-no-target-blank": ["error", { allowReferrer: true }],
    "react/no-unescaped-entities": "off",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",
    "require-await": "error",
    "sort-imports": "error",
    "sort-vars": "error",
    "todo-plz/ticket-ref": [
      "error",
      {
        pattern: "(API|CP|EMPLOYER|POL|PORTAL|PFMLPB)-[0-9]+",
        terms: ["TODO"],
      },
    ],
    // We use _.get() a lot to get deeply nested nullable values
    "you-dont-need-lodash-underscore/get": "off",
  },
  settings: {
    jest: {
      version: "detect",
    },
    jsdoc: {
      mode: "typescript",
    },
    react: {
      version: "detect",
    },
  },
};
