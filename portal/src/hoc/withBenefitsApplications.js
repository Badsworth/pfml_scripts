import React, { useEffect } from "react";
import BenefitsApplicationCollection from "../models/BenefitsApplicationCollection";
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
const withBenefitsApplications = (Component) => {
  const ComponentWithClaims = (props) => {
    const { appLogic } = props;
    const { users } = appLogic;
    const { t } = useTranslation();

    assert(appLogic.benefitsApplications);
    // Since we are within a withUser higher order component, user should always be set
    assert(users.user);

    const benefitsApplications =
      appLogic.benefitsApplications.benefitsApplications;
    const shouldLoad = !appLogic.benefitsApplications.hasLoadedAll;

    useEffect(() => {
      if (shouldLoad) {
        appLogic.benefitsApplications.loadAll();
      }

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [shouldLoad]);

    if (shouldLoad) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner
            aria-valuetext={t(
              "components.withBenefitsApplications.loadingLabel"
            )}
          />
        </div>
      );
    }

    return <Component {...props} claims={benefitsApplications} />;
  };

  ComponentWithClaims.propTypes = {
    appLogic: PropTypes.shape({
      users: PropTypes.shape({
        user: PropTypes.instanceOf(User).isRequired,
      }).isRequired,
      benefitsApplications: PropTypes.shape({
        benefitsApplications: PropTypes.instanceOf(
          BenefitsApplicationCollection
        ),
        hasLoadedAll: PropTypes.bool.isRequired,
        loadAll: PropTypes.func.isRequired,
      }).isRequired,
      appErrors: PropTypes.object.isRequired,
    }).isRequired,
  };

  return withUser(ComponentWithClaims);
};

export default withBenefitsApplications;
