import Heading from "./Heading";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * The ReviewRow component encapsulates a single reviewable row of form data.
 */
const ReviewRow = (props) => {
  const classes = classnames(
    "margin-bottom-2 padding-bottom-2 display-flex flex-justify",
    {
      "border-bottom-2px border-base-lighter": !props.noBorder,
    }
  );

  return (
    <div className={classes} data-testid={props["data-testid"]}>
      <div className="margin-right-2">
        <Heading level={props.level} size="4" className="margin-bottom-1">
          {props.label}
        </Heading>
        {props.children}
      </div>
      {props.editHref && (
        <Link href={props.editHref}>
          <a
            className="usa-link"
            aria-label={`${props.editText}: ${props.label}`}
          >
            {props.editText}
          </a>
        </Link>
      )}
      {props.action}
    </div>
  );
};

ReviewRow.propTypes = {
  /**
   * Renders an element (e.g. a button or link) which the user can interact with.
   * If undefined, no element will be shown.
   */
  action: PropTypes.node,
  /**
   * The content you want the user to review
   */
  children: PropTypes.node.isRequired,
  /**
   * Identifier for querying this row in tests.
   */
  "data-testid": PropTypes.string,
  /**
   * HTML `href` attribute for the edit link.
   * If undefined, no edit link will be shown.
   */
  editHref: PropTypes.string,
  /**
   * Localized text for the edit link
   */
  editText: PropTypes.node,
  /**
   * Label describing the content to be reviewed. This is also
   * read to screen readers when they interact with the edit link.
   */
  label: PropTypes.node.isRequired,
  /**
   * The heading level to use for the label
   */
  level: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
  /** Exclude the bottom border. Useful if a child already includes a border. */
  noBorder: PropTypes.bool,
};

export default ReviewRow;
