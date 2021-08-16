import Button from "./Button";
import ButtonLink from "./ButtonLink";
import PropTypes from "prop-types";
import React from "react";
import tracker from "../services/tracker";
import { useTranslation } from "../locales/i18n";

/**
 * Help users go back to the previous page in a multi-page transaction. The
 * intention is to alleviate concerns that going back will result in lost data.
 */
function BackButton(props) {
  const { t } = useTranslation();
  const label = props.label || t("components.backButton.label");
  const behaveLikeBrowserBackButton = !props.href;
  const historyApi = props.history || globalThis.history;

  /**
   * Don't render a Back button if there's no page in the history to go back to
   */
  if (
    behaveLikeBrowserBackButton &&
    (typeof historyApi === "undefined" || historyApi.length <= 1)
  ) {
    return null;
  }

  const handleClick = () => {
    tracker.trackEvent("BackButton clicked", { behaveLikeBrowserBackButton });
    if (behaveLikeBrowserBackButton) {
      historyApi.back();
    }
  };

  let Component, componentProps;
  if (props.href) {
    Component = ButtonLink;
    componentProps = {
      href: props.href,
    };
  } else {
    Component = Button;
  }

  return (
    <Component
      {...componentProps}
      onClick={handleClick}
      className="margin-bottom-5"
      variation="unstyled"
    >
      <svg
        className="margin-right-05"
        height="12"
        width="12"
        viewBox="0 0 448 512"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          fill="currentColor"
          d="M257.5 445.1l-22.2 22.2c-9.4 9.4-24.6 9.4-33.9 0L7 273c-9.4-9.4-9.4-24.6 0-33.9L201.4 44.7c9.4-9.4 24.6-9.4 33.9 0l22.2 22.2c9.5 9.5 9.3 25-.4 34.3L136.6 216H424c13.3 0 24 10.7 24 24v32c0 13.3-10.7 24-24 24H136.6l120.5 114.8c9.8 9.3 10 24.8.4 34.3z"
        />
      </svg>
      {label}
    </Component>
  );
}

BackButton.propTypes = {
  label: PropTypes.string,
  href: PropTypes.string,
  /**
   * Pass in the History API instance to be used for
   * navigating backwards and determining what's in
   * history. Mostly here to support unit testing.
   */
  history: PropTypes.object,
};

export default BackButton;
