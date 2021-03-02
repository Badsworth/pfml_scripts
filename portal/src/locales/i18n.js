/**
 * @file Setup and configure all internationalization frameworks, including setting the same language.
 * @see docs/internationalization.md
 */
import englishLocale from "./app/en-US";
import formatValue from "./formatters";
import i18next from "i18next";
import { initReactI18next } from "react-i18next";
import tracker from "../services/tracker";

const defaultLocale = "en-US";

/**
 * Track when an i18n key is missing a value.
 * @param {string[]} locales - language codes
 * @param {string} namespace
 * @param {string} key
 * @param {string} fallbackValue
 * @returns {string}
 */
function missingKeyHandler(locales, namespace, key, fallbackValue) {
  tracker.trackEvent("Missing i18n", {
    i18nKey: key,
    i18nLocales: locales,
    i18nNamespace: namespace,
  });

  return fallbackValue;
}

/**
 * Initialize I18n libraries for the App
 * @param {string} locale - locale that matches localization file (e.g "en-US")
 * @param {object} resources - mappings of locale codes and corresponding content strings
 * @returns {Promise<Function>} resolves with the t() function
 */
export const initializeI18n = (
  locale = defaultLocale,
  resources = { "en-US": englishLocale }
) => {
  return i18next
    .use(initReactI18next) // passes the i18n instance to react-i18next which will make it available for all the components via the context api.
    .init({
      debug: process.env.NODE_ENV === "development",
      fallbackLng: defaultLocale,
      interpolation: {
        escapeValue: false, // react already escapes values
        format: formatValue,
      },
      lng: locale,
      missingKeyHandler,
      resources,
      saveMissing: true, // required in order for missingKeyHandler to work
    });
};

/**
 * Translation function for use outside of a react context
 * translations will not automatically rerender on language change
 * @see https://www.i18next.com/overview/api#t
 * @param {string} key - locales key for translation string
 * @param {object} context - data that can be interpolated with string
 * @returns {string} translation string
 */
export const t = (key, context) => i18next.t(key, context);

/**
 * React hook that creates a `t` function for functional components
 * and HOC for use in class components
 * @see https://react.i18next.com/latest/usetranslation-hook
 * @see https://react.i18next.com/latest/withtranslation-hoc
 */
export { useTranslation, withTranslation } from "react-i18next";
