import Button from "./Button";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "../locales/i18n";

/**
 * Displays auth links and info about the user if they're logged in
 */
const AuthNav = (props) => {
  const { t } = useTranslation();
  const user = props.user || {};

  return (
    <div className="text-right">
      <div className="grid-container">
        <div className="grid-row">
          <div className="grid-col-fill margin-y-1">
            {user.email_address ? (
              <React.Fragment>
                <span className="display-inline-block margin-right-1">
                  {user.email_address}
                </span>
                <Button
                  className="width-auto"
                  inversed
                  onClick={props.onLogout}
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
  onLogout: PropTypes.func.isRequired,
};

export default AuthNav;
