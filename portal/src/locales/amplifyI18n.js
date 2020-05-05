import { I18n } from "aws-amplify";
import englishLocale from "./amplify/en-US";

const authScreenLabels = {
  "en-US": englishLocale,
};

/**
 *
 * Configuration for authentication screen i18n, including English (US) string overrides.
 * @see https://aws-amplify.github.io/docs/js/i18n and docs/internationalization.md
 * @param {string} locale - language and region combination, e.g. 'pt-BR' for Portuguese of Brazil
 */
const setAmplifyI18n = (locale) => {
  I18n.putVocabularies(authScreenLabels);
  I18n.setLanguage(locale);
};

export default setAmplifyI18n;
