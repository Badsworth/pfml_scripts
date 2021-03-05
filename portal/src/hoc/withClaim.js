import React, { useEffect } from "react";
import ClaimCollection from "../models/ClaimCollection";
import PropTypes from "prop-types";
import Spinner from "../components/Spinner";
import User from "../models/User";
import assert from "assert";
import { useTranslation } from "../locales/i18n";
import withUser from "./withUser";

/**
 * Higher order component that loads a claim if not yet loaded,
 * then adds a single claim to the wrapped component based on query parameters
 * @param {React.Component} Component - Component to receive claim prop
 * @returns {React.Component} - Component with claim prop
 */
const withClaim = (Component) => {
  const ComponentWithClaim = (props) => {
    const { appLogic, query } = props;
    const { t } = useTranslation();

    assert(appLogic.claims);
    // Since we are within a withUser higher order component, user should always be set
    assert(appLogic.users.user);

    const application_id = query.claim_id;
    const claims = appLogic.claims.claims;
    const claim = claims.getItem(application_id);
    const shouldLoad = !appLogic.claims.hasLoadedClaimAndWarnings(
      application_id
    );

    useEffect(() => {
      if (shouldLoad) {
        appLogic.claims.load(application_id);
      }

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [shouldLoad]);

    if (shouldLoad) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner aria-valuetext={t("components.withClaims.loadingLabel")} />
        </div>
      );
    }

    return <Component {...props} claim={claim} />;
  };

  ComponentWithClaim.propTypes = {
    appLogic: PropTypes.shape({
      users: PropTypes.shape({
        user: PropTypes.instanceOf(User).isRequired,
      }).isRequired,
      claims: PropTypes.shape({
        claims: PropTypes.instanceOf(ClaimCollection),
        load: PropTypes.func.isRequired,
        hasLoadedClaimAndWarnings: PropTypes.func.isRequired,
      }).isRequired,
      appErrors: PropTypes.object.isRequired,
    }).isRequired,
    query: PropTypes.shape({
      claim_id: PropTypes.string.isRequired,
    }).isRequired,
  };

  return withUser(ComponentWithClaim);
};

export default withClaim;
