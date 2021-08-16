import PropTypes from "prop-types";
import React from "react";

/**
 * A details element that expands and collopses.
 */
function Details(props) {
  return (
    <details className="c-details">
      <summary className="margin-bottom-2 text-primary text-underline font-ui-xs">
        {props.label}
      </summary>
      <div className="margin-bottom-2">{props.children}</div>
    </details>
  );
}

Details.propTypes = {
  /**
   * Clickable label that summarizes the content.
   */
  label: PropTypes.string.isRequired,
  /**
   * Content to be expanded.
   */
  children: PropTypes.node.isRequired,
};

export default Details;
