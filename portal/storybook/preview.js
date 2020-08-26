/**
 * @file Storybook uses this file to globally control the rendering of a story.
 * "Preview" as in the "preview iFrame."
 * @see https://medium.com/storybookjs/declarative-storybook-configuration-49912f77b78
 */

// Apply global styling to our stories
import "../styles/app.scss";

import { initializeI18n } from "../src/locales/i18n";

// Internationalize strings in our stories
initializeI18n();

export const parameters = {
  options: {
    // Sort stories alphabetically
    storySort: {
      method: "alphabetical",
    },
  },
};
