import { Auth } from "aws-amplify";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "react-i18next";

/**
 * Displays auth links and info about the user if they're logged in
 * @returns {React.Component}
 */
const AuthNav = props => {
  const { t } = useTranslation();

  const handleSignOut = () => {
    Auth.signOut();
  };

  if (props.user) {
    return (
      <React.Fragment>
        {t("components.authNav.loggedInUserLabel", { user: props.user })}
        <nav>
          <button onClick={handleSignOut}>
            {t("components.authNav.logOutButtonText")}
          </button>
        </nav>
      </React.Fragment>
    );
  }
};

AuthNav.propTypes = {
  user: PropTypes.shape({
    username: PropTypes.string
  })
};

export default AuthNav;
