/**
 * @file Storybook uses this file to globally control the rendering of a story.
 * "Preview" as in the "preview iFrame."
 * @see https://medium.com/storybookjs/declarative-storybook-configuration-49912f77b78
 */

// Apply global styling to our stories
import "../styles/app.scss";

import React from "react";
import { I18nextProvider } from "react-i18next";
import { addDecorator } from "@storybook/react";
import i18n from "../src/i18n";

// Internationalize strings in our stories
addDecorator(storyFn => (
  <I18nextProvider i18n={i18n}>
    <div className="usa-prose">{storyFn()}</div>
  </I18nextProvider>
));
