import Icon from "./Icon";
import PropTypes from "prop-types";
import React from "react";

/**
 * Alert bar displayed at the very top of a page
 */
const AlertBar = (props) => {
  const { children } = props;

  return (
    <div className="padding-y-2 bg-warning">
      <div className="grid-container">
        <div className="grid-row">
          <div className="grid-col">
            <div className="display-flex">
              <i className="margin-right-2">
                <Icon name="bell_ring" size={4} />
              </i>
              <p className="margin-0 text-ink">{children}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

AlertBar.propTypes = {
  /**
   * Text/HTML for alert message.
   */
  children: PropTypes.node.isRequired,
};

export default AlertBar;
