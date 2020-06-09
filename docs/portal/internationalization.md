# Internationalization

All Portal internationalization (i18n) is configured in the `portal/src/locales/i18n.js` module. This includes both application and auth screen i18n; these systems are separate due to Amplify's restrictions on auth screen customization.

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

### Conventions

Internationalization content can get messy and lead to hard-to-find bugs during translation. As such we strictly follow the below conventions to preserve readability, maintainability, and avoid errors.

#### Organization

- Keys are organized under four top-level objects by how they're used: `components`, `pages`, `errors` and `shared`.
- `components` and `pages` define content used in specific components and pages, respectively. `errors` contains content used in error messages, which aren’t page or component specific. `shared` defines content shared between multiple components or pages.
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

### Basic usage with hook

```js
import React from "react";
import { useTranslation } from "react-i18next";

export function MyComponent() {
  const { t } = useTranslation();

  return <p>{t("translationResourceKey")}</p>;
}
```

## Auth screens

To override the default language on Amplify auth screens, and provide i18n for other locales, we are using the [Amplify I18n](https://aws-amplify.github.io/docs/js/i18n) module. Their documentation is not the greatest, and to find the locale keys to override, you may need to find their references in the [corresponding Amplify React component](https://github.com/aws-amplify/amplify-js/tree/master/packages/aws-amplify-react/src/Auth) by searching the component file for `I18n.get`.
