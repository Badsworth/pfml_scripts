import PropTypes from "prop-types";
import React from "react";
import { Trans } from "react-i18next";
import classnames from "classnames";

/**
 * Banner displayed at the top of the Dashboard 
 * in case the user has accidentally created an employee account and
 * instead of an employer account
 */
const ConvertToEmployerBanner = (props) => {
  const link = props.link
  const classes = classnames(
    "bg-yellow padding-1 margin-bottom-2 text-center"
  );

  return (
    <React.Fragment>
      <div role="alert" className={classes}>
        <Trans
          i18nKey="components.convertToEmployerBanner.message"
          components={{
            "convert-link": (
              <a
                data-cy="convert-link"
                href={link}
              />
            ),
          }}
        />
      </div>
    </React.Fragment>
  );
};

ConvertToEmployerBanner.propTypes = {
   link: PropTypes.string,
};

export default ConvertToEmployerBanner;
