import Button from "./Button";
import PropTypes from "prop-types";
import React from "react";
import tracker from "../services/tracker";
import useThrottledHandler from "../hooks/useThrottledHandler";

/**
 * Renders a Button with a throttled onClick handler. The onClick property should be an
 * async function to be called when a user clicks the button. While the onClick function is
 * running asynchronously the button will show a loading state.
 */
function ThrottledButton({ onClick, ...props }) {
  const handleClick = useThrottledHandler(async (event) => {
    event.preventDefault();

    const resp = onClick();
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

ThrottledButton.propTypes = {
  "aria-controls": PropTypes.string,
  "aria-expanded": PropTypes.oneOf(["true", "false"]),
  /**
   * Button text
   */
  children: PropTypes.node.isRequired,
  /**
   * Additional classes to apply to the HTML element. Useful for adding
   * utility classes to control spacing.
   */
  className: PropTypes.string,
  /**
   * Display a loading message alongside the button
   */
  loadingMessage: PropTypes.string,
  /**
   * Apply the "inverse" style modifier
   */
  inversed: PropTypes.bool,
  /**
   * HTML `name` attribute
   */
  name: PropTypes.string,
  /**
   * HTML `onClick` attribute
   */
  onClick: PropTypes.func,
  /**
   * HTML `type` attribute
   */
  type: PropTypes.oneOf(["button", "submit"]),
  /**
   * Disable button click
   */
  disabled: PropTypes.bool,
  /**
   * Change the default button style
   */
  variation: PropTypes.oneOf([
    "accent-cool",
    "outline",
    "secondary",
    "unstyled",
  ]),
};

export default ThrottledButton;
