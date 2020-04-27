import { Auth } from "aws-amplify";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "../locales/i18n";

/**
 * Displays auth links and info about the user if they're logged in
 */
const AuthNav = (props) => {
  const { t } = useTranslation();

  const handleSignOut = () => {
    Auth.signOut();
  };

  const user = props.user || {};

  return (
    <div className="bg-primary font-body-sm text-white text-right">
      <div className="grid-container">
        <div className="grid-row">
          <div className="grid-col-fill margin-y-1">
            {user.username ? (
              <React.Fragment>
                <span className="display-inline-block margin-right-1">
                  {user.username}
                </span>
                <button
                  className="usa-button usa-button--outline usa-button--inverse usa-button--unstyled width-auto"
                  onClick={handleSignOut}
                  type="button"
                >
                  {t("components.authNav.logOutButtonText")}
                </button>
              </React.Fragment>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};

AuthNav.propTypes = {
  user: PropTypes.shape({
    username: PropTypes.string,
  }),
};

export default AuthNav;
