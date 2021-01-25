/* eslint-disable react/prop-types */
/**
 * @file Playroom uses this file to globally control the rendering of its previews.
 * "Preview" as in the "preview iFrame."
 */
import "../styles/app.scss";
import React from "react";
import { initializeI18n } from "../src/locales/i18n";

// Internationalize strings in our components
initializeI18n();

/**
 * Container component for our Playroom previews.
 * The code written in Playroom is rendered within this,
 * which provides some basic structure to the preview.
 * @returns {React.Component}
 */
export default ({ children }) => (
  <main className="grid-container margin-y-2">
    <div className="grid-row">
      <div className="grid-col-fill">{children}</div>
    </div>
  </main>
);
