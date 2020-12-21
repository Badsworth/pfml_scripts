import PropTypes from "prop-types";
import React from "react";
import { Trans } from "react-i18next";

/**
 * Banner displayed at the top of the site to indicate the site
 * does not support the current web browser, when the user is
 * using Internet Explorer versions 11 and below.
 */
const UnsupportedBrowserBanner = (props) => {
  const containerClassName = "c-unsupported-browser-banner";

  /**
   * Render inline css so there's never a flash of this banner on supported
   * browsers while other CSS loads. The @media query will only work for IE 11 and below.
   */
  const inlineStyles = props.forceRender
    ? null
    : `.${containerClassName} { display: none } @media all and (-ms-high-contrast: none), (-ms-high-contrast: active) { .${containerClassName} { display: block } }`;

  /**
   * The @media query approach above doesn't work for IE 9 and below, and conditional HTML
   * comments don't work for IE10 and above, so we use a combination:
   */
  const conditionalHTMLComment = `<!--[if lte IE 9]><style>.${containerClassName} { display: block }</style><![endif]-->`;

  return (
    <React.Fragment>
      <style>{inlineStyles}</style>
      <span dangerouslySetInnerHTML={{ __html: conditionalHTMLComment }} />
      <div
        role="alert"
        className={`${containerClassName} bg-yellow padding-1 text-center`}
      >
        <Trans
          i18nKey="components.unsupportedBrowserBanner.message"
          components={{
            "update-link": (
              <a
                href="https://browser-update.org/update.html"
                target="_blank"
                rel="noreferrer noopener"
              />
            ),
          }}
        />
      </div>
    </React.Fragment>
  );
};

UnsupportedBrowserBanner.propTypes = {
  /**
   * Force the banner to render regardless of whether the
   * browser is supported or not. Useful for testing or
   * previewing the component in a supported browser.
   **/
  forceRender: PropTypes.bool,
};

export default UnsupportedBrowserBanner;
