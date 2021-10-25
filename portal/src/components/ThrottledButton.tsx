import Button from "./Button";
import React from "react";
import tracker from "../services/tracker";
import useThrottledHandler from "../hooks/useThrottledHandler";

interface ThrottledButtonProps {
  "aria-controls"?: string;
  "aria-expanded"?: "true" | "false";
  /**
   * Button text
   */
  children: React.ReactNode;
  /**
   * Additional classes to apply to the HTML element. Useful for adding
   * utility classes to control spacing.
   */
  className?: string;
  /**
   * Display a loading message alongside the button
   */
  loadingMessage?: string;
  /**
   * Apply the "inverse" style modifier
   */
  inversed?: boolean;
  /**
   * HTML `name` attribute
   */
  name?: string;
  /**
   * HTML `onClick` attribute
   */
  onClick?: (Event: React.SyntheticEvent) => Promise<void>;
  /**
   * HTML `type` attribute
   */
  type?: "button" | "submit";
  /**
   * Disable button click
   */
  disabled?: boolean;
  /**
   * Change the default button style
   */
  variation?: "accent-cool" | "outline" | "secondary" | "unstyled";
}

/**
 * Renders a Button with a throttled onClick handler. The onClick property should be an
 * async function to be called when a user clicks the button. While the onClick function is
 * running asynchronously the button will show a loading state.
 */
function ThrottledButton({ onClick, ...props }: ThrottledButtonProps) {
  const handleClick = useThrottledHandler(async (event) => {
    event.preventDefault();

    const resp = onClick(event);
    if (!(resp instanceof Promise)) {
      tracker.trackEvent(
        "onClick wasn't a Promise, so user isn't seeing a loading indicator."
      );
      // eslint-disable-next-line no-console
      console.warn("onClick should be a Promise");
    }
    await resp;
  });

  return (
    <Button
      onClick={handleClick}
      loading={handleClick.isThrottled}
      {...props}
    ></Button>
  );
}

export default ThrottledButton;
