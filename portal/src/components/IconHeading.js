import Heading from "./Heading";
import Icon from "./Icon";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

const IconHeading = ({ children, name }) => {
  /**
   * Using name to determine correct flex
   * and color settings
   */
  const { color, flexAlign } = {
    check_circle: { color: "text-green", flexAlign: "flex-align-start" },
    cancel: { color: "text-red", flexAlign: "flex-align-center" },
  }[name];

  return (
    <Heading
      className={classnames("display-flex", "flex-row", flexAlign)}
      level="2"
      size="3"
    >
      <Icon
        className={classnames("margin-right-2px", "flex-auto", color)}
        name={name}
        fill="currentColor"
        size={3}
      />
      <span className="flex-1">{children}</span>
    </Heading>
  );
};

IconHeading.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node,
  ]).isRequired,
  name: PropTypes.string.isRequired,
};

export default IconHeading;
