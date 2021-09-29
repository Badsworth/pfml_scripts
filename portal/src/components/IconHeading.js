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
    check: { color: "text-green", flexAlign: "flex-align-start" },
    close: { color: "text-red", flexAlign: "flex-align-center" },
  }[name];

  return (
    <Heading
      className={classnames("display-flex", "flex-row", flexAlign)}
      level="2"
      size="3"
    >
      <Icon
        className={classnames("margin-right-2px", color)}
        name={name}
        fill="currentColor"
        size={3}
      />
      {children}
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
