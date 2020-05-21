import { Auth } from "aws-amplify";
import Button from "./Button";
import PropTypes from "prop-types";
import React from "react";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * Displays auth links and info about the user if they're logged in
 */
const AuthNav = (props) => {
  const { t } = useTranslation();

  const handleSignOut = async () => {
    await Auth.signOut();

    // Force a page reload so that any local app state is cleared
    window.location.assign(routes.home);
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
                <Button
                  className="width-auto"
                  inversed
                  onClick={handleSignOut}
                  variation="unstyled"
                >
                  {t("components.authNav.logOutButton")}
                </Button>
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
