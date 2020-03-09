import { Auth } from "aws-amplify";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "react-i18next";

/**
 * Displays auth links and info about the user if they're logged in
 */
const AuthNav = props => {
  const { t } = useTranslation();

  const handleSignOut = () => {
    Auth.signOut();
  };

  if (props.user) {
    return (
      <div className="bg-primary font-body-sm text-white text-right">
        <div className="grid-container">
          <div className="grid-row">
            <div className="grid-col-fill margin-y-1">
              <span className="display-inline-block margin-right-1">
                {props.user.username}
              </span>
              <button
                className="usa-button usa-button--outline usa-button--inverse usa-button--unstyled width-auto"
                onClick={handleSignOut}
              >
                {t("components.authNav.logOutButtonText")}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
};

AuthNav.propTypes = {
  user: PropTypes.shape({
    username: PropTypes.string,
  }),
};

export default AuthNav;
