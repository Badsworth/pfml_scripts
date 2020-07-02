# Portal Development

This page covers development practices for working on the Mass PFML Portal. Please document liberally so that others may benefit from your learning.

## Creating a page

All files in the [`portal/srcs/pages`](../../portal/src/pages) directory are automatically available as routes based on their name, e.g. `about.js` is routed to `/about`. Files named `index.js` are routed to the root of the directory. See more at the Next.js docs on [routing](https://nextjs.org/docs/routing/introduction) and [pages](https://nextjs.org/docs/basic-features/pages).

1. Each time you add a new page, add a new route to [`src/routes.js`](../../portal/src/routes.js).
1. If the page is part of a question flow, add the page to the relevant step in [`src/flows/leave-application.js`](../../portal/src/flows/leave-application.js)
1. Add content strings for the page to [`src/locales/app/en-US.js`](../../portal/src/locales/app/en-US.js).
1. Add a test file for the page (and for any new components) to [`__tests__`](../../portal/__tests__/)

## `next.config.js`

The [`next.config.js`](https://nextjs.org/docs/api-reference/next.config.js/introduction) file is a Node.js module that can be used to configure build and export behavior, such as Webpack settings.
