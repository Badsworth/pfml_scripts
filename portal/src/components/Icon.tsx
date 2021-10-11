import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
/**
 * SVG icon from the U.S. Web Design System
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/icons/)
 */
function Icon(props) {
  const usaIconClass = props.size ? `usa-icon--size-${props.size}` : "usa-icon";
  const className = classnames(usaIconClass, props.className);

  return (
    <svg
      className={className}
      aria-hidden="true"
      focusable="false"
      role="img"
      fill={props.fill}
    >
      <use xlinkHref={`/img/sprite.svg#${props.name}`} />
    </svg>
  );
}
Icon.propTypes = {
  /** Name of the the USWDS Icon to render */
  name: PropTypes.string.isRequired,
  className: PropTypes.string,
  fill: PropTypes.string,
  size: PropTypes.number,
};
export default Icon;
