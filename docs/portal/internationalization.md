# Internationalization

All Portal internationalization (i18n) is configured in the `portal/src/locales/i18n.js` module. This includes both application and auth screen i18n; these systems are separate due to Amplify's restrictions on auth screen customization.

The locale selection for both i18n systems is configured in `i18n.js` to allow locale synchronization across the app.

## Application
This app uses [i18next](https://i18next.com/) and its [react library](https://react.i18next.com/) for application localization. You can find i18next translation resources in `portal/locales/`. Each language has a file with a set of keys and values for every content string we need to localize for our site. The keys are how we will refer to these strings throughout our codebase, rather than hard coding the content strings.

### Tips for contributors adding keys to resources:
- Keys must be unique - there can't be two keys with the same name.
- Try to name keys after the purpose of the key, not just an underscored version of your translation. This may result in duplication of translations (i.e. multiple keys for "First name"), but this is much more flexible for cases down the line when one of those translations needs to change (i.e "First name" changes to "Spouse's first name").
- Keys must be alphabetical so it's easier for others to find and update.
- Keys can be nested. If a content string is unique to a page or component, nest within a page/component key.

### Basic usage with hook

```javascript
import React from 'react';
import { useTranslation } from 'react-i18next';

export function MyComponent() {
  const { t } = useTranslation();

  return <p>{t('translationResourceKey')}</p>
}
```

## Auth screens

To override the default language on Amplify auth screens, and provide i18n for other locales, we are using the [Amplify I18n](https://aws-amplify.github.io/docs/js/i18n) module. Their documentation is not the greatest, and to find the locale keys to override, you may need to find their references in the [corresponding Amplify React component](https://github.com/aws-amplify/amplify-js/tree/master/packages/aws-amplify-react/src/Auth) by searching the component file for `I18n.get`.
