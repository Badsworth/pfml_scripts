import englishLocale from "./app/en-US";
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  "en-US": englishLocale,
};

/**
 * Setup the application internationalization framework, which
 * is what we'll then use for rendering locale strings in our UI.
 * This does not include Amplify authentication screen i18n, which is configured by `./amplifyI18n.js`.
 * @see https://react.i18next.com/ and docs/internationalization.md
 * @param {string} locale - language and region combination, e.g. 'pt_BR' for Portuguese of Brazil
 * @param {string} fallbackLocale - locale to fallback to in case the designated locale is unavailable
 */
const setAppI18n = (locale, fallbackLocale = locale) => {
  i18n
    .use(initReactI18next) // passes the i18n instance to react-i18next which will make it available for all the components via the context api.
    .init({
      debug: process.env.NODE_ENV === "development",
      fallbackLng: fallbackLocale,
      interpolation: {
        escapeValue: false, // react already escapes values
      },
      lng: locale,
      resources,
    });
};

export default setAppI18n;
