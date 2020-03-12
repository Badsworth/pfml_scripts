/* eslint sort-keys: "error" */
import styleTokens from "../utils/styleTokens";

const tokens = styleTokens();

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
  },
  toast: {
    background: tokens["color-info-darker"],
    borderBottom: `${tokens["spacer-multiple"]} solid ${tokens["color-warning"]}`,
    fontSize: tokens["body-font-size"],
  },
};

export default theme;
