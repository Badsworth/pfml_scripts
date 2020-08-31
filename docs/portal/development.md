# Portal Development

This page covers development practices for working on the Mass PFML Portal. Please document liberally so that others may benefit from your learning.

## TODO comments

Our linter enforces that TODO comments include a reference to a Jira ticket that tracks the work to implement the TODO. The expected format of a TODO is:

```
TODO (CP-123): Message
```

...where `CP-123` is the Jira ticket number.

**Why?** We want to avoid losing track of work that we haven't completed, and unintentionally ship an application that doesn't work end-to-end. Making sure that we have tickets in our backlog is one major way we can avoid losing track of this work. In addition, having ticket references within TODO comments provides an engineer a way to learn additional context, and potentially learn that the work has already been completed, but the TODO got left behind in the code by accident.

## Creating a page

All files in the [`portal/src/pages`](../../portal/src/pages) directory are automatically available as routes based on their name, e.g. `about.js` is routed to `/about`. Files named `index.js` are routed to the root of the directory. See more at the Next.js docs on [routing](https://nextjs.org/docs/routing/introduction) and [pages](https://nextjs.org/docs/basic-features/pages).

For Employer-specific pages, files will be nested in an [`/employers`](../../portal/src/pages/employers) subdirectory.

1. Each time you add a new page, add a new route to [`src/routes.js`](../../portal/src/routes.js).
1. Add content strings for the page to [`src/locales/app/en-US.js`](../../portal/src/locales/app/en-US.js).
1. Add a test file for the page (and for any new components) to [`tests`](../../portal/tests/)

### Question Page Routing

We use a [state machine](https://statecharts.github.io/) to control routing between question pages in a flow. The library we use behind the scenes for this is [XState](https://xstate.js.org/docs/).

1. Add a new state for the route to [`src/flows/claimaint.js`](../../portal/src/flows/claimant.js). Include the `step` and `fields` to the state's `meta` object and add a `CONTINUE` transition. Read more on xstate configs [here](https://xstate.js.org/docs/guides/transitions.html#machine-transition-method).
1. If routing to or from the page is conditional, you'll need to define `guard`s that determine the state. Read more on xstate guards [here](https://xstate.js.org/docs/guides/guards.html#guards-condition-functions).
1. Add a test state for the new page to the `machineTests` object in [`tests/flows/claimant.test.js`](../../portal/tests/flows/claimant.test.js)
1. If routing is conditional, add items with appropriate data to the `testData` array.

### Auth Pages Routing

Similar to Question Pages, pages used in the Auth flow are also in the [`/portal/src/pages`](../../portal/src/pages/) subdirectory, but routing is controlled using the state machine.

1. Add a new state for the route to [`src/flows/auth.js`](../../portal/src/flows/auth.js). Include a `CONTINUE` transition.
1. If routing to or from the page is conditional, you'll need to define `guard`s that determine the state. Read more on xstate guards [here](https://xstate.js.org/docs/guides/guards.html#guards-condition-functions).
1. Add a test state for the new page to the `machineTests` object in [`tests/flows/auth.test.js`](../../portal/tests/flows/auth.test.js)
1. If routing is conditional, add items with appropriate data to the `testData` array.

## `next.config.js`

The [`next.config.js`](https://nextjs.org/docs/api-reference/next.config.js/introduction) file is a Node.js module that can be used to configure build and export behavior, such as Webpack settings.
