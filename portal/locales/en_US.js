/**
 *
 * @file US English language file.
 * @see docs/internationalization.md
 *
 */

const pages = {};

const components = {
  authNav: {
    logOutButtonText: "Log out",
    loggedInUserLabel: "Logged in as: {{user.username}}"
  },
  header: {
    skipToContent: "Skip to main content",
    appTitle: "Paid Family and Medical Leave"
  }
};

const englishLocale = {
  translation: Object.assign({}, { components, pages })
};

export default englishLocale;
