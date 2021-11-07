# TypeScript

Portal's source code is written in [TypeScript](https://www.typescriptlang.org/). TypeScript is a typed superset of JavaScript that compiles to plain JavaScript.

The [TypeScript landing page](https://www.typescriptlang.org/) does a good job of describing TypeScript, and how it relates to JavaScript. Give it a scroll.

> Portal was originally written in JavaScript and later migrated to TypeScript in October 2021. You can [reference the original migration tech spec in Confluence](https://lwd.atlassian.net/l/c/JYP9mGFr) for additional context.

## Conventions and norms

1. **Use `interface` instead of `class` for data models that have no getters, setters, or default values.** This simplifies the code and results in less compiled JavaScript.
1. **Portal data models should match the API's.** For example, if an API model indicates a field is `nullable` / `Optional`, the corresponding Portal data model should reflect the field can be `null` as well. Our type declarations should be as narrow as possible however, and we should be comfortable questioning if an API data model field is truly ever empty in reality.

   - [View the API's schema here](https://paidleave-api-test.mass.gov/api/docs/)
   - [View an overview of the API DB models here](../api/technical-overview.md)

1. **Explicitly declaring function return types is encouraged**. This helps make the engineer's intent clear. We're not currently enforcing this [with a lint rule](https://github.com/typescript-eslint/typescript-eslint/blob/master/packages/eslint-plugin/docs/rules/explicit-function-return-type.md), since this can produce a lot of noise due to React functional components and hooks. It's solvable, but was [deprioritized](https://lwd.atlassian.net/browse/PORTAL-935?focusedCommentId=56295) during the initial TypeScript migration effort.
1. **Avoid TypeScript features that produce different JS code when compiled** when there is a suitable alternative. For example, we avoid using TypeScript's [`enum`](https://www.typescriptlang.org/docs/handbook/enums.html) and [parameter properties](https://www.typescriptlang.org/docs/handbook/2/classes.html#parameter-properties). Lint rules are configured to prevent those two particular examples. Why? ⤵️

   > TypeScript is supposed to be JavaScript, but with static type features added. If we remove all of the types from TypeScript code, what's left should be valid JavaScript code. The formal word used in the TypeScript documentation is "type-level extension": most TypeScript features are type-level extensions to JavaScript, but they don't affect the code's runtime behavior. Unfortunately, TypeScript's solution is to break its own rule in this case [for enums]. When compiling an enum, the compiler adds extra JavaScript code that never existed in the original TypeScript code. There are very few TypeScript features like this. Each of these unusual features adds a confusing complication to the otherwise simple TypeScript compiler model. — Execute Program's TypeScript course.

## Tricky errors & solutions

### Writing boolean expressions

The [strict-boolean-expressions](https://github.com/typescript-eslint/typescript-eslint/blob/master/packages/eslint-plugin/docs/rules/strict-boolean-expressions.md) lint rule is enforced, and can be confusing when initially encountered.

Before this rule, we could (and did) have conditions that would check if a number was set, for instance:

```ts
const size: number = props.size;
const className = size ? `margin-${size}` : "margin-5";
```

A bug is present in that example, because `0` is falsey in JavaScript, so if `size` was `0`, `className` would be `margin-5` (the fallback) instead of `margin-0`.

With the lint rule, this is now an error indicating:

> Unexpected nullable number value in conditional. Please handle the nullish/zero/NaN cases explicitly.

You can now fix the lint error with a few approaches.

1. [Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing_operator):

   ```ts
   const className = `margin-${size ?? 5}`;
   ```

1. Using the `isBlank` utility:

   ```ts
   const className = isBlank(size) ? "margin-5" : `margin-${size}`;
   ```

### Handling null/undefined values

`null` and `undefined` have their own distinct types and you’ll get a type error if you try to use them where a concrete value is expected.

For example with this TypeScript code, `users.find` has no guarantee that it will actually find a user, but you can write code as though it will:

```ts
declare const loggedInUsername: string;

const users = [
  { name: "Oby", age: 12 },
  { name: "Heera", age: 32 },
];

const loggedInUser = users.find((u) => u.name === loggedInUsername);
console.log(loggedInUser.age);
```

You'll receive an error that you have not made a guarantee that the `loggedInUser` exists before trying to use it. One approach to solving this is to use the [optional chaining operator](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining):

```ts
console.log(loggedInUser?.age);
```

> This behavior is due to [`strictNullChecks`](https://www.typescriptlang.org/tsconfig#strictNullChecks).

### Narrowing an object's type

TypeScript supports narrowing objects by [using the `in` operator](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#the-in-operator-narrowing).

For example:

```ts
interface ErrorWithIssues {
  issues: string[];
}

interface BlankError {}

function handleError(error: ErrorWithIssues | BlankError) {
  if ("issues" in error) {
    // We've now narrowed error down to ErrorWithIssues
    console.error(error.issues.join(","));
  } else {
    // We've now narrowed error down to BlankError
    console.error("Generic error occurred");
  }
}
```

## Learning TypeScript

Crash courses and references

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [TypeScript Playground](https://www.typescriptlang.org/play/)
- [React TypeScript Cheatsheets](https://react-typescript-cheatsheet.netlify.com/)

More in depth course material

- [Execute Program](https://www.executeprogram.com/courses/typescript-basics)
- [Effective TypeScript](https://effectivetypescript.com/)
