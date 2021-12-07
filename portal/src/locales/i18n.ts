/**
 * @file Setup and configure all internationalization frameworks, including setting the same language.
 * @see docs/internationalization.md
 */
import i18next, { FormatFunction, Resource } from "i18next";
import bytesToMb from "../utils/bytesToMb";
import englishLocale from "./app/en-US";
import formatValue from "./formatters";
import { initReactI18next } from "react-i18next";
import tracker from "../services/tracker";

const defaultLocale = "en-US";

/**
 * Track when an i18n key is missing a value.
 */
function missingKeyHandler(
  locales: readonly string[],
  namespace: string,
  key: string,
  fallbackValue: string
) {
  tracker.trackEvent("Missing i18n", {
    i18nKey: key,
    i18nLocales: JSON.stringify(locales),
    i18nNamespace: namespace,
  });

  return fallbackValue;
}

/**
 * Initialize I18n libraries for the App
 * @param locale - locale that matches localization file (e.g "en-US")
 * @param resources - mappings of locale codes and corresponding content strings
 */
export const initializeI18n = (
  locale: string = defaultLocale,
  resources: Resource = { "en-US": englishLocale }
) => {
  return i18next
    .use(initReactI18next) // passes the i18n instance to react-i18next which will make it available for all the components via the context api.
    .init(
      {
        debug: process.env.NODE_ENV === "development",
        fallbackLng: defaultLocale,
        interpolation: {
          defaultVariables: {
            fileSizeMaxMB: bytesToMb(
              Number(process.env.fileSizeMaxBytesFineos)
            ),
          },
          escapeValue: false, // react already escapes values
          format: formatValue as FormatFunction,
        },
        lng: locale,
        missingKeyHandler,
        resources,
        saveMissing: true, // required in order for missingKeyHandler to work
      },
      undefined
    );
};

/**
 * Translation function for use outside of a react context
 * translations will not automatically rerender on language change
 * @see https://www.i18next.com/overview/api#t
 */
export const t = (key: string, options?: string | { [key: string]: unknown }) =>
  i18next.t(key, options);

/**
 * React hook that creates a `t` function for functional components
 * and HOC for use in class components
 * @see https://react.i18next.com/latest/usetranslation-hook
 * @see https://react.i18next.com/latest/withtranslation-hoc
 */
export { useTranslation, withTranslation } from "react-i18next";
