/**
 * @file Setup and configure all internationalization frameworks, including setting the same language.
 * @see docs/internationalization.md
 */
import i18next from "i18next";
import setAmplifyI18n from "./amplifyI18n";
import setAppI18n from "./appI18n";

const defaultLocale = "en_US";

/**
 * Initialize I18n libraries for Amplify and the App
 * @param {string} locale - locale that matches localization file (e.g "en_us")
 * @returns {object} - I18n instances for app (appI18n) and amplify (amplifyI18n)
 */
export const initializeI18n = (locale = defaultLocale) => {
  const appI18n = setAppI18n(locale);
  const amplifyI18n = setAmplifyI18n(locale);

  return {
    appI18n,
    amplifyI18n,
  };
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
