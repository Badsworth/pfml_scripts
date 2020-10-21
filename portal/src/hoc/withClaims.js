import React, { useEffect } from "react";
import PropTypes from "prop-types";
import Spinner from "../components/Spinner";
import User from "../models/User";
import assert from "assert";
import { useTranslation } from "../locales/i18n";
import withUser from "./withUser";

/**
 * Higher order component that provides the current user's claims to the wrapped component.
 * The higher order component also loads the claims if they have not already been loaded.
 * @param {React.Component} Component - Component to receive claims prop
 * @returns {React.Component} - Component with claims prop
 */
const withClaims = (Component) => {
  const ComponentWithClaims = (props) => {
    const { appLogic } = props;
    const { users } = appLogic;
    const { t } = useTranslation();

    assert(appLogic.claims);
    // Since we are within a withUser higher order component, user should always be set
    assert(users.user);

    useEffect(() => {
      if (!appLogic.claims.claims) {
        appLogic.claims.loadAll();
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [appLogic.claims.claims]);

    if (!appLogic.claims.claims) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner aria-valuetext={t("components.withClaims.loadingLabel")} />
        </div>
      );
    } else {
      return <Component {...props} claims={appLogic.claims.claims} />;
    }
  };

  ComponentWithClaims.propTypes = {
    appLogic: PropTypes.shape({
      users: PropTypes.shape({
        user: PropTypes.instanceOf(User).isRequired,
      }).isRequired,
      claims: PropTypes.shape({
        loadAll: PropTypes.func.isRequired,
      }).isRequired,
      appErrors: PropTypes.object.isRequired,
    }).isRequired,
  };

  return withUser(ComponentWithClaims);
};

export default withClaims;
