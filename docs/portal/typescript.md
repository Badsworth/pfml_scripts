# TypeScript

Portal's source code is written in [TypeScript](https://www.typescriptlang.org/). TypeScript is a typed superset of JavaScript that compiles to plain JavaScript.

The [TypeScript landing page](https://www.typescriptlang.org/) does a good job of describing TypeScript, and how it relates to JavaScript. Give it a scroll.

> Portal was originally written in JavaScript and later migrated to TypeScript in October 2021. You can [reference the original migration tech spec in Confluence](https://lwd.atlassian.net/l/c/JYP9mGFr) for additional context.

## Conventions

- We avoid TypeScript features that produce different JS code when compiled when there is a suitable alternative, for example we avoid using TypeScript's [`enum`](https://www.typescriptlang.org/docs/handbook/enums.html) and [parameter properties](https://www.typescriptlang.org/docs/handbook/2/classes.html#parameter-properties). Lint rules are configured to prevent those two particular examples. Why? ⤵️
  > TypeScript is supposed to be JavaScript, but with static type features added. If we remove all of the types from TypeScript code, what's left should be valid JavaScript code. The formal word used in the TypeScript documentation is "type-level extension": most TypeScript features are type-level extensions to JavaScript, but they don't affect the code's runtime behavior. Unfortunately, TypeScript's solution is to break its own rule in this case [for enums]. When compiling an enum, the compiler adds extra JavaScript code that never existed in the original TypeScript code. There are very few TypeScript features like this. Each of these unusual features adds a confusing complication to the otherwise simple TypeScript compiler model. — Execute Program's TypeScript course.

## Learning TypeScript

Crash courses and references

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [TypeScript Playground](https://www.typescriptlang.org/play/)
- [React TypeScript Cheatsheets](https://react-typescript-cheatsheet.netlify.com/)

More in depth course material

- [Execute Program](https://www.executeprogram.com/courses/typescript-basics)
- [Effective TypeScript](https://effectivetypescript.com/)
