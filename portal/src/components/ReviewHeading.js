import Heading from "./Heading";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";

/**
 * Heading for a group of ReviewRow components
 */
const ReviewHeading = (props) => {
  return (
    <div className="display-flex flex-align-end margin-top-6 margin-bottom-3">
      <Heading
        className="flex-fill margin-right-1"
        id={props.id}
        level={props.level}
        size="2"
      >
        {props.children}
      </Heading>
      {props.editHref && (
        <Link href={props.editHref}>
          <a
            className="usa-link margin-0"
            aria-label={`${props.editText}: ${props.children}`}
          >
            {props.editText}
          </a>
        </Link>
      )}
    </div>
  );
};

ReviewHeading.propTypes = {
  /**
   * Heading text
   */
  children: PropTypes.string.isRequired,
  /**
   * HTML `href` attribute for the edit link.
   * If undefined, no edit link will be shown.
   */
  editHref: PropTypes.string,
  /**
   * Localized text for the edit link
   */
  editText: PropTypes.node,
  // TODO this
  id: PropTypes.string,
  /**
   * The heading level to use
   */
  level: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
};

export default ReviewHeading;
