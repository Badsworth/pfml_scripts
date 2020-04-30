/* eslint sort-keys: "error" */

/**
 * Design tokens (type, color, spacing). These are based on design tokens from
 * our Mayflower-themed U.S. Web Design System implementation, which lives
 * in our .scss files.
 *
 * TODO: Override type and color styles by overriding Amplify CSS variables
 * https://lwd.atlassian.net/browse/CP-247
 */
const tokens = {
  "body-font-family": "Texta, Helvetica, sans-serif",
  "body-font-size": "1.21rem",
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
    fontSize: "1.21rem",
    textDecoration: "underline",
  },
  button: {
    backgroundColor: tokens["color-primary"],
    color: "#fff",
    fontSize: tokens["body-font-size"],
    fontWeight: "bold",
    lineHeight: "1",
    padding: "0.75rem 1.25rem",
    textTransform: "none",
  },
  formContainer: {
    marginTop: "0px",
    textAlign: "left",
  },
  formSection: {
    background: "none",
    boxShadow: "none",
    maxWidth: 460, // provide a bit more breathing room on desktop
    paddingLeft: "0px",
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
    padding: "0.5rem",
  },
  inputLabel: {
    color: tokens["color-base-ink"],
    fontSize: tokens["body-font-size"],
  },
  sectionFooter: {
    flexDirection: "column",
  },
  sectionFooterPrimaryContent: {
    margin: "0 0 16px",
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
    // Toast component is used to display error messages, however its
    // styling options are limited and its markup is inaccessible. We
    // use our own error component, so we hide this component.
    display: "none",
  },
};

export default theme;
