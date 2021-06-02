import PropTypes from "prop-types";
import React from "react";
import { Trans } from "react-i18next";
import classnames from "classnames";

/**
 * Banner displayed at the top of the site to indicate upcoming
 * scheduled maintenance.
 */
const UpcomingMaintenanceBanner = (props) => { // props.show, props.start, props.end
  const classes = classnames("upcoming-maintenance-banner bg-yellow padding-1 text-center",
  {
    "display-block": props.show === true,
  });

  return (
    <React.Fragment>
      <div role="alert" className={classes}>
        <Trans
          i18nKey="components.upcomingMaintenanceBanner.message"
          components={{
            start: props.start,
            end: props.end
          }}
        />
      </div>
    </React.Fragment>
  );
};

UpcomingMaintenanceBanner.propTypes = {
  /**
   * Boolean used to show the message
   **/
  show: PropTypes.bool,
  /**
   * Start date string for the message
   **/
  start: PropTypes.string,
  /**
   * End date string for the message
   **/
  end: PropTypes.string
};

export default UpcomingMaintenanceBanner;
