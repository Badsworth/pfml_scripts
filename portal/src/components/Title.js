import Head from "next/head"; // https://nextjs.org/docs/api-reference/next/head
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * A page title. This also sets the title displayed in search engines and
 * the browser tab. There should only be one of these per page!
 */
const Title = ({ component = "h1", small = false, ...props }) => {
  const TitleElement = component;
  const classes = classnames("margin-top-0 margin-bottom-2", {
    "font-heading-lg line-height-sans-2": !small,
    "font-heading-sm line-height-sans-3": small,
    "usa-legend": component === "legend",
  });
  const seoTitle = props.seoTitle ? props.seoTitle : props.children;

  return (
    <React.Fragment>
      <Head>
        <title>{seoTitle}</title>
      </Head>
      <TitleElement className={classes}>{props.children}</TitleElement>
    </React.Fragment>
  );
};

Title.propTypes = {
  /**
   * Title text
   */
  children: PropTypes.node.isRequired,
  /**
   * HTML element used to render the page title
   */
  component: PropTypes.oneOf(["h1", "legend"]),
  /**
   * By default, the text you pass in is also used for the title displayed
   * in search engines and the browser tab. This can be overridden by setting
   * this prop.
   */
  seoTitle: PropTypes.string,
  /**
   * Enable the smaller title variant, which is used as a "section" title
   * for sets of question pages.
   */
  small: PropTypes.bool,
};

export default Title;
