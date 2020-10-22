/**
 * @file Setup and configure all internationalization frameworks, including setting the same language.
 * @see docs/internationalization.md
 */
import englishLocale from "./app/en-US";
import i18next from "i18next";
import { initReactI18next } from "react-i18next";

const defaultLocale = "en-US";

/**
 * Initialize I18n libraries for the App
 * @param {string} locale - locale that matches localization file (e.g "en-US")
 */
export const initializeI18n = (locale = defaultLocale) => {
  i18next
    .use(initReactI18next) // passes the i18n instance to react-i18next which will make it available for all the components via the context api.
    .init({
      debug: process.env.NODE_ENV === "development",
      fallbackLng: defaultLocale,
      interpolation: {
        escapeValue: false, // react already escapes values
        format: function (value, format) {
          // formats number into currency (e.g. 1000 -> $1,000.00)
          if (format === "currency") {
            return new Intl.NumberFormat("en-US", {
              style: "currency",
              currency: "USD",
            }).format(value);
          }
          return value;
        },
      },
      lng: locale,
      resources: {
        "en-US": englishLocale,
      },
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
