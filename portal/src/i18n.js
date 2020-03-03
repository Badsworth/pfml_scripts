/**
 * @file Setup and configure our internationalization framework, which
 * is what we'll then use for rendering locale strings in our UI.
 * @see https://react.i18next.com/ and docs/internationalization.md
 */

import englishLocale from "./locales/en_US";
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const defaultLanguage = "en-US";
const resources = {
  "en-US": englishLocale
};

i18n
  .use(initReactI18next) // passes the i18n instance to react-i18next which will make it available for all the components via the context api.
  .init({
    debug: process.env.NODE_ENV === "development",
    fallbackLng: defaultLanguage,
    interpolation: {
      escapeValue: false // react already escapes values
    },
    lng: defaultLanguage,
    resources
  });

export default i18n;
