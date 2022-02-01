/**
 * @file Visual examples of the Mayflower-themed U.S. Web Design System
 * color tokens.
 */
import React, { useEffect, useRef, useState } from "react";

export default {
  title: "Misc/Colors",
};

const Swatch = ({ token }: { token: string }) => {
  const bgClass = `bg-${token}`;
  const bgElement = useRef<HTMLDivElement>(null);
  const [colorValue, setColor] = useState("");

  useEffect(() => {
    if (bgElement.current instanceof HTMLElement) {
      const { backgroundColor } = window.getComputedStyle(bgElement.current);
      if (backgroundColor) setColor(backgroundColor);
    }
  }, [bgElement]);

  return (
    <div className="width-card margin-bottom-4">
      <div className={`${bgClass} height-card`} ref={bgElement} />
      <code className="font-mono-3xs">.{bgClass}</code>
      <br />
      <code className="font-mono-3xs">.text-{token}</code>
      <br />
      <code className="font-mono-3xs text-base">{colorValue}</code>
    </div>
  );
};

export const Swatches = () => {
  // Viewing this code sample in Storybook is likely not that useful.
  // A better reference is the visual example that is rendered by it.
  const families = {
    base: [
      "base-lightest",
      "base-lighter",
      "base",
      "base-dark",
      "base-darkest",
      "ink",
    ],
    primary: [
      "primary-lighter",
      "primary-light",
      "primary",
      "primary-dark",
      "primary-darker",
    ],
    secondary: [
      "secondary-lighter",
      "secondary-light",
      "secondary",
      "secondary-dark",
      "secondary-darker",
    ],
    error: [
      "error-lighter",
      "error-light",
      "error",
      "error-dark",
      "error-darker",
    ],
    warning: ["warning-lighter", "warning-light", "warning"],
    success: [
      "success-lighter",
      "success-light",
      "success",
      "success-dark",
      "success-darker",
    ],
    info: ["info-lighter", "info-light", "info", "info-dark", "info-darker"],
  };

  return (
    <React.Fragment>
      {Object.entries(families).map(([family, tokens]) => {
        return (
          <section key={family}>
            <h2 className="font-size-lg">{family}</h2>
            <div className="grid-row flex-wrap">
              {tokens.map((token) => (
                <Swatch key={token} token={token} />
              ))}
            </div>
          </section>
        );
      })}
    </React.Fragment>
  );
};
