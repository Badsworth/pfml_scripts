import PropTypes from "prop-types";
import React from "react";
import { Trans } from "react-i18next";
import classnames from "classnames";

/**
 * Banner displayed at the top of the site to indicate the site
 * does not support the current web browser, when the user is
 * using Internet Explorer versions 11 and below.
 */
const UnsupportedBrowserBanner = (props) => {
  const classes = classnames(
    "c-unsupported-browser-banner bg-yellow padding-1 text-center",
    {
      "display-block": props.forceRender === true,
    }
  );

  /**
   * The CSS @media query approach doesn't work for IE 9 and below, and conditional HTML
   * comments don't work for IE10 and above, so we use a combination. IE9 and below doesn't
   * support Content-Security-Policy, so we don't need to worry about that with this inline <style>:
   */
  const conditionalHTMLComment = `<!--[if lte IE 9]><style>.c-unsupported-browser-banner { display: block }</style><![endif]-->`;

  return (
    <React.Fragment>
      <span dangerouslySetInnerHTML={{ __html: conditionalHTMLComment }} />
      <div role="alert" className={classes}>
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
   */
  forceRender: PropTypes.bool,
};

export default UnsupportedBrowserBanner;
