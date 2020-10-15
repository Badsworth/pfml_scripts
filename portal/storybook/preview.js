/**
 * @file Storybook uses this file to globally control the rendering of a story.
 * "Preview" as in the "preview iFrame."
 * @see https://medium.com/storybookjs/declarative-storybook-configuration-49912f77b78
 */
import "../styles/app.scss"; // Apply global styling to our stories
import { addDecorator } from "@storybook/react";
import { initializeI18n } from "../src/locales/i18n";
import { withNextRouter } from "storybook-addon-next-router";

// Internationalize strings in our stories
initializeI18n();

// Support components that use next/router
addDecorator(withNextRouter());

export const parameters = {
  options: {
    // Sort stories alphabetically
    storySort: {
      method: "alphabetical",
    },
  },
};
