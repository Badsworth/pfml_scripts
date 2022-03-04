# Internationalization

All Portal internationalization (i18n) is configured in the `portal/src/locales/i18n.js` module.

The locale selection for both i18n systems is configured in `i18n.js` to allow locale synchronization across the app.

## Application

This app uses [i18next](https://i18next.com/) and its [React library](https://react.i18next.com/) for application localization. You can find i18next translation resources in `portal/locales/app/`. Each language has a file with a set of keys and values for every content string we need to localize for our site. The keys are how we will refer to these strings throughout our codebase, rather than hard coding the content strings.

### i18next patterns

Our application takes advantage of some advanced patterns supported by the `i18next` library. It can be useful to be aware of these while working in the codebase:

- [Context](https://www.i18next.com/translation-function/context) allows us to have variations of a string based on the value of a `context` property:

  ```js
  t("haveIncome", { context: "married" }); // -> "Do you or your spouse have income sources?"
  ```

  ```json
  {
    "haveIncome": "Do you have income sources?",
    "haveIncome_married": "Do you or your spouse have income sources?"
  }
  ```

- The [Trans](https://react.i18next.com/latest/trans-component) component allows us to integrate html tags such as links (`<a>` tags) and text formatting tags (e.g. `<strong>` or `<em>`) into translated text:

  ```jsx
  <Trans
    i18nKey="userAgreement"
    components={{
      "consent-link": (
        <a href="https://www.mass.gov/paidleave-informedconsent" />
      ),
      "privacy-policy-link": <a href="https://www.mass.gov/privacypolicy" />,
    }}
  />
  ```

  ```json
  {
    "userAgreement": "To find out more about how the Commonwealth might use the information you share with DFML, please read the <consent-link>DFML Informed Consent Agreement</consent-link> and the <privacy-policy-link>Privacy Policy for Mass.gov</privacy-policy-link>."
  }
  ```

  Note that we are using the [alternative usage of Trans introduced in v11.6.0](https://react.i18next.com/latest/trans-component#alternative-usage-v-11-6-0) where components are passed in as props rather than as children of `Trans`. This method allows the use of named tags in locale strings rather than needing to refer to child components by their index.

- [Formatters](https://www.i18next.com/translation-function/formatting) are functions that define locale-specific formats for specially-formatted values such as currencies or time durations.

  ```js
  t("timeDuration", { minutes: 480 }); // -> "8h"
  t("timeDuration", { minutes: 475 }); // -> "7h 55m"
  ```

  ```js
  function formatValue(value, format, locale) {
    if (format === "hoursMinutesDuration") {
      // Could also internationalize by using the locale value
      const { hours, minutes } = convertMinutesToHours(value);
      if (minutes === 0) return `${hours}h`;
      return `${hours}h ${minutes}m`;
    }
    return value;
  ```

  ```json
  {
    "timeDuration": "{{minutes, hoursMinutesDuration}}"
  }
  ```

### Conventions

Internationalization content can get messy and lead to hard-to-find bugs during translation. As such we strictly follow the below conventions to preserve readability, maintainability, and avoid errors.

#### Organization

- Keys are organized under top-level objects by how they're used:
  - `components` defines content used in specific components
  - `pages` defines content used in specific pages
  - `errors` defines content used in [error messages](./error-handling.md), which aren’t page or component specific
  - `shared` defines content shared between multiple components or pages
  - `chars` defines special characters (such as non-breaking spaces, which are difficult to distinguish in values)
- Keys are limited to three levels deep, for example `pages.claimsDateOfBirth.title`. This makes the structure easier to navigate and the process of finding a specific element more consistent.

#### Naming

- Prioritize readability, and then brevity.
- Try to be consistent with existing keys. For example the title content for each page should be under a key, `pages.<page-identifier>.title`.
- When a page is related to a larger series of pages you can indicate that with a prefix. For example, the name form page within the claims flow is identified as `pages.claimsName`.
- Avoid repeating context in the key. For example, prefer `pages.claimsName.sectionHint` over `pages.claimsName.nameSectionHint`.
- Try to name keys after the purpose of the key, not just an underscored version of your translation. This may result in duplication of translations (i.e. multiple keys for "First name"), but this is much more flexible for cases down the line when one of those translations needs to change (i.e "First name" changes to "Spouse's first name").
- Keys should be alphabetical so they're easier for others to find and update. We also considered sorting them by page-order where they occur but alphabetical is more easily enforced (with linting) and doesn’t require re-ordering even if content on a page is re-ordered.
- Keys must be unique - there can't be two keys with the same name. This only applies to the entire key, for example having `pages.claimsName.sectionHint` and `pages.claimsSsn.sectionHint` is fine.

##### Common page element terminology

The PFML pages follow a design system that uses common terms for various page elements. It's helpful to use these terms when defining content strings for both the developer experience (when implementing a page design this gives you tips on how to name content strings) and in tracing content from the page back to the i18n key. These terms may change over time so this will need to be updated when they do. Some common element terms include:

- `title` - one per page
- `sectionLabel` - one per section or fieldset. This is typically either an HTML legend or label, depending on the page/section
- `lead` - additional context about an entire page, section, or fieldset
- `legend` - context about an embedded fieldset (note that sectionLabel content is always called sectionLabel even if we render it with an HTML legend element)
- `label` - typically one per input
- `hint` - additional context about a specific input

**Note:** we use `snake_case` for input field names to match the names used by the API, but we don’t carry that over to i18n keys. For example the `state_id` field on the claims license page has a label called `pages.claimsLicense.stateIdLabel`.

For visual examples of different text elements on a page see the design team’s [page template](https://www.figma.com/file/v8LlmK8r1JmByqtNVMvqjS/PFML?node-id=938%3A0) designs.

#### Sharing content

All shared keys are located inside the `shared` object; this makes it obvious that when you're changing one of them your changes will impact multiple components/pages. This is meant to prevent accidental content changes if someone is only trying to update content in one place.

Sharing content should follow this pattern:

- The shared content is defined with a key inside the `shared` object.
- Each page or component that uses the shared content should define its own key and reference the shared key.
- Shared keys, such as `shared.claimsPages.leaveTypeTitle`, shouldn't be referenced directly in application code.

##### Example

```
shared: {
  claimsPages:
    // Define the shared key here -- anyone changing this will know it affects multiple pages
    takingLeaveTitle: "Who is taking leave?",
  },
}

pages: {
  claimsName: {
    // Reference the shared content with a key where it's used. This key, `pages.claimsName.title`,
    // will be the key used within the page. This makes it easy to stop using the shared content
    // by changing this to a content string.
    title: "$t(shared.claimsPages.takingLeaveTitle)",
  },
}
```

#### Using markup in values

Sometimes content necessitates the use of specific HTML tags. However, markup should only include tag names and not tag attributes. A tag's `className`, `href`, and other attributes should be set by the page or component that renders the key (see usage example below).

Using markup in content strings can be useful but it can also make them more difficult to read and edit without introducing errors. Markup should be used sparingly. Some of the reasons for using markup in content strings include answering yes to any of these questions:

- Does this content require specific embedded tags for formatting? (e.g. `<a>`, `<em>`, `<strong>`, `<ul>`, `<ol>`, or multiple `<p>` tags)
- Does this content serve one primary function for the user?
- Is it helpful to edit this content as one key? (e.g. two paragraphs that serve one purpose for the user, or list items with an explicit order)
- Would breaking this content into multiple keys make them more difficult to name semantically or add unnecessary structure?

### Rendering values in pages and components

#### Using the `useTranslation` hook

With simple values, you only need to get the `t` function to render values in the functional component:

```js
import React from "react";
import { useTranslation } from "react-i18next";

export function MyComponent() {
  const { t } = useTranslation();

  return <p>{t("translationResourceKey")}</p>;
}
```

#### The `Trans` component

Since the `t` function can't be used for values that include markup, the `Trans` component is used to interpolate or translate complex react elements.

Set the key in the language file, excluding all tag attributes:

```
htmlKey:
  "<ul><li>List item one</li><li>List item two has <my-link>a link</my-link></li></ul>",
```

Anchors are given a unique tag name in the language file, and the corresponding `href` value is defined in `routes.js`:

```js
myLink: "http://www.example.com",
```

The `Trans` component renders the basic tags, `br`, `strong`, `i`, and `p`. However, other tags must be explicitly defined. The `components` object is where attributes such as `className`, `href` can be set:

```js
import React from "react";
import { Trans } from "react-i18next";

<Trans
  i18nKey="htmlKey"
  components={{
    "my-link": (
      <a target="_blank" rel="noopener" href={routes.external.myLink} />
    ),
    ul: <ul className="usa-list" />,
    li: <li />,
  }}
/>;
```
