import Heading from "./Heading";
import PropTypes from "prop-types";
import React from "react";

/**
 * Heading for a group of ReviewRow components
 */
const ReviewHeading = (props) => {
  return (
    <div className="display-flex flex-align-end margin-top-6 margin-bottom-3">
      <Heading className="flex-fill margin-right-1" level="2">
        {props.children}
      </Heading>
      {props.editHref && (
        <a
          className="usa-link margin-0"
          href={props.editHref}
          aria-label={`${props.editText}: ${props.children}`}
        >
          {props.editText}
        </a>
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
};

export default ReviewHeading;
