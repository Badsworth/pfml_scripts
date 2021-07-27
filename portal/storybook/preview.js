/* eslint-disable react/prop-types */
/**
 * @file Storybook uses this file to globally control the rendering of a story.
 * "Preview" as in the "preview iFrame."
 * @see https://medium.com/storybookjs/declarative-storybook-configuration-49912f77b78
 */
import "../styles/app.scss"; // Apply global styling to our stories
import { Anchor, DocsContainer } from "@storybook/addon-docs/blocks";
import React from "react";
import { initializeI18n } from "../src/locales/i18n";

// Internationalize strings in our stories
initializeI18n();

const CustomContainer = ({ children, context }) => (
  <DocsContainer context={context}>
    <Anchor storyId={context.id} />
    {children}
  </DocsContainer>
);

export const parameters = {
  docs: {
    // Prevent Storybook from scrolling to the bottom of a long story
    // https://github.com/storybookjs/storybook/issues/10983#issuecomment-708599819
    container: CustomContainer,
  },
  options: {
    // Sort stories alphabetically
    storySort: {
      method: "alphabetical",
    },
  },
};
