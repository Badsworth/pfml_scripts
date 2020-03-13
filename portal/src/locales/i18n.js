/**
 * @file Setup and configure all internationalization frameworks, including setting the same language.
 * @see docs/internationalization.md
 */

import setAmplifyI18n from "./amplifyI18n";
import setAppI18n from "./appI18n";

const defaultLocale = "en_US";

const appI18n = setAppI18n(defaultLocale);
const amplifyI18n = setAmplifyI18n(defaultLocale);

const i18n = {
  appI18n,
  amplifyI18n,
};

export default i18n;
