/* eslint sort-keys: "error" */

/**
 * Design tokens (type, color, spacing). These are based on design tokens from
 * our Mayflower-themed U.S. Web Design System implementation, which lives
 * in our .scss files.
 *
 * TODO: I don't like this, but it's the least fragile option
 * currently (see https://lwd.atlassian.net/browse/CP-146). In the future,
 * we should strive to create a source of truth for these design tokens, rather
 * than having some of them duplicated between our Sass files and this JS file.
 */
const tokens = {
  "body-font-family": "Texta, Helvetica, sans-serif",
  "body-font-size": "1.13rem",
  "color-base": "#707070",
  "color-base-dark": "#535353",
  "color-base-ink": "#141414",
  "color-info-darker": "#0A2B48",
  "color-primary": "#14558f",
  "color-warning": "#f6c51b",
  "h1-font-size": "2.11rem",
  "input-line-height": "1.1",
  "spacer-multiple": "8px",
};

/**
 * A custom Amplify UI theme to match the look of the rest of our site
 * @see https://aws-amplify.github.io/docs/js/authentication#customize-ui-theme
 * @see https://github.com/aws-amplify/amplify-js/blob/master/packages/aws-amplify-react/src/Amplify-UI/Amplify-UI-Theme.tsx
 */
const theme = {
  a: {
    color: tokens["color-primary"],
    textDecoration: "underline",
  },
  button: {
    backgroundColor: tokens["color-primary"],
    fontSize: tokens["body-font-size"],
    fontWeight: "bold",
    padding: "0.75rem 1.25rem",
    textTransform: "none",
  },
  formSection: {
    maxWidth: 550, // provide a bit more breathing room on desktop
  },
  hint: {
    color: tokens["color-base"],
    fontSize: tokens["body-font-size"],
  },
  input: {
    borderColor: tokens["color-base-dark"],
    borderRadius: 0,
    borderWidth: 1,
    color: tokens["color-base-ink"],
    fontSize: tokens["body-font-size"],
    lineHeight: tokens["input-line-height"],
  },
  inputLabel: {
    color: tokens["color-base-ink"],
    fontSize: tokens["body-font-size"],
  },
  sectionFooterSecondaryContent: {
    color: tokens["color-base"],
    fontSize: tokens["body-font-size"],
    fontWeight: "bold",
  },
  sectionHeaderContent: {
    color: tokens["color-base-ink"],
    fontSize: tokens["h1-font-size"],
    fontWeight: "bold",
  },
  toast: {
    background: tokens["color-info-darker"],
    borderBottom: `${tokens["spacer-multiple"]} solid ${tokens["color-warning"]}`,
    fontSize: tokens["body-font-size"],
  },
};

export default theme;
