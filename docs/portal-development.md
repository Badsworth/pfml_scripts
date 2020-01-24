### Introduction

This page covers development practices for working on the Mass PFML front-end portal. Please document liberally so that others may benefit from your learning.

### Creating a page

All files in the `portal/pages/` directory are automatically available as routes based on their name, e.g. `about.js` is routed to `/about`. Files named `index.js` are routed to the root of the directory. See more at the Next.js docs on [routing](https://nextjs.org/docs/routing/introduction) and [pages](https://nextjs.org/docs/basic-features/pages).

Each time you add a new page, update the `exportPathMap` in `next.config.js`. Without this, static HTML routing will not include the new page.

### Custom advanced behavior via `next.config.js`

The [`next.config.js`](https://nextjs.org/docs/api-reference/next.config.js/introduction) file is a Node.js module that can be used to configure advanced behavior, such as Webpack settings. Route exporting also lives here.