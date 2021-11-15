import { Helmet } from "react-helmet"; // we don't use next/head because of https://lwd.atlassian.net/browse/CP-1071
import React from "react";
import classnames from "classnames";

interface TitleProps {
  /**
   * Title text
   */
  children: React.ReactNode;
  /**
   * HTML element used to render the page title
   */
  component?: "h1" | "legend";
  /** Visually hide the title */
  hidden?: boolean;
  /** Override default bottom margin */
  marginBottom?: "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8";
  /**
   * By default, the text you pass in is also used for the title displayed
   * in search engines and the browser tab. This can be overridden by setting
   * this prop.
   */
  seoTitle?: string;
  /**
   * Enable the smaller title variant, which is used as a "section" title
   * for sets of question pages.
   */
  small?: boolean;
  /** Override default font weight */
  weight?: "normal" | "bold";
}

/**
 * A page title. This also sets the title displayed in search engines and
 * the browser tab. There should only be one of these per page!
 */
const Title = ({ component = "h1", small = false, ...props }: TitleProps) => {
  const TitleElement = component;
  const marginBottom = props.marginBottom ? props.marginBottom : "2";

  const classes = classnames(
    `js-title margin-top-0 margin-bottom-${marginBottom}`,
    {
      "font-heading-lg line-height-sans-2": !small,
      "font-heading-sm line-height-sans-3": small,
      "text-normal": props.weight === "normal",
      "usa-legend": component === "legend",
      "usa-sr-only": !!props.hidden,
    }
  );
  const seoTitle = props.seoTitle ? props.seoTitle : props.children;

  return (
    <React.Fragment>
      <Helmet>
        <title>{seoTitle}</title>
      </Helmet>
      <TitleElement tabIndex={-1} className={classes}>
        {props.children}
      </TitleElement>
    </React.Fragment>
  );
};

export default Title;
