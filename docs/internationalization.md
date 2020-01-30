# Internationalization

This app uses [i18next](https://i18next.com/) and its [react library](https://react.i18next.com/) for localization. You can find i18next translation resources in `portal/locales/`. Each language has a file with a set of keys and values for every content string we need to localize for our site. The keys are how we will refer to these strings throughout our codebase, rather than hard coding the content strings.


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
