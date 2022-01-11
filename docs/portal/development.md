# Portal Development

This page covers development practices for working on the Mass PFML Portal. Please document liberally so that others may benefit from your learning.

## TODO comments

Our linter enforces that TODO comments include a reference to a Jira ticket that tracks the work to implement the TODO. The expected format of a TODO is:

```
TODO (PORTAL-123): Message
```

...where `PORTAL-123` is the Jira ticket number.

**Why?** We want to avoid losing track of work that we haven't completed, and unintentionally ship an application that doesn't work end-to-end. Making sure that we have tickets in our backlog is one major way we can avoid losing track of this work. In addition, having ticket references within TODO comments provides an engineer a way to learn additional context, and potentially learn that the work has already been completed, but the TODO got left behind in the code by accident.

## Creating a page

All files in the [`portal/src/pages`](../../portal/src/pages) directory are automatically available as routes based on their name, e.g. `about.js` is routed to `/about`. Files named `index.js` are routed to the root of the directory. See more at the Next.js docs on [routing](https://nextjs.org/docs/routing/introduction) and [pages](https://nextjs.org/docs/basic-features/pages).

For Employer-specific pages, files will be nested in an [`/employers`](../../portal/src/pages/employers) subdirectory.

1. Each time you add a new page, add a new route to [`src/routes.js`](../../portal/src/routes.js).
1. Add content strings for the page to [`src/locales/app/en-US.js`](../../portal/src/locales/app/en-US.js).
1. Add a test file for the page (and for any new components) to [`tests`](../../portal/tests/)

### Question Pages

We use a [state machine](https://statecharts.github.io/) to control routing between question pages in a flow. The library we use behind the scenes for this is [XState](https://xstate.js.org/docs/).

1. Add a new state node for the route to [`src/flows/claimaint.js`](../../portal/src/flows/claimant.js), and add a `CONTINUE` transition. Read more on XState configs [here](https://xstate.js.org/docs/guides/transitions.html#machine-transition-method).
1. Within a `meta` object on the state node, add a `step` and `fields` properties. The `fields` value should contain the field paths for every field that may be displayed on the question page. This is important because this array is what's used for determining what validation errors should display on the question page, and also is used for identifying when a step on the checklist is In Progress or Completed.
1. If the page should display validation issues for specific rules, add an array of `applicableRules` to the state's `meta` object.
1. If routing to or from the page is conditional, you'll need to define `guards` that determine the state. Read more on xstate guards [here](https://xstate.js.org/docs/guides/guards.html#guards-condition-functions).
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

## Frontend <> Backend Configuration
The default developer experience is that your local portal server connects to the backend staging environment. If you wish to connect your local portal to local backend run `npm run dev:local` from portal (paired with `make logs-local` in the api directory in order to run the local configured api server for the backend).

Gotchas and tips for local-to-local setup:

- Use an email address where you can receive the verification code during account creation e.g. `slinky+local+dev@navapbc.com`. We connect to a real aws cognito instance even during local development.
- Make sure you've [seeded your database](https://github.com/EOLWD/pfml/tree/main/api#seed-your-database). Additionally, when testing some flows locally (i.e. application submit), you will need a wages and contributions record in your local db for the employee/employer pairing you're using. In order to pass validation checks, enter FEIN/SSN combination generated by your generate_wagesandcontributions.py script.

For historical context:

- [Environment Switching Tech Spec](https://lwd.atlassian.net/wiki/spaces/CP/pages/2144436299/Environment+Switching+Tech+Spec) 
- [How to connect local to local manually](https://lwd.atlassian.net/wiki/spaces/DD/pages/2126872748/Local+Portal+to+Local+API+Development) (Should not need now that commands are available)