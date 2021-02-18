import React, { useEffect } from "react";
import EmployerClaim from "../models/EmployerClaim";
import PropTypes from "prop-types";
import { Spinner } from "../components/Spinner";
import User from "../models/User";
import assert from "assert";
import { isFeatureEnabled } from "../services/featureFlags";
import routes from "../../src/routes";
import { useTranslation } from "react-i18next";
import withUser from "./withUser";

/**
 * Higher order component that (1) loads a claim if not yet loaded and adds a single claim to the wrapper component
 * based on query parameters, and (2) redirects to Verify Business page if an unverified employer exists.
 * This should be used in routes meant for employers.
 * @param {React.Component} Component - Component to receive claim prop
 * @returns {React.Component} component with claim prop
 */
const withEmployerClaim = (Component) => {
  const ComponentWithClaim = (props) => {
    const { appLogic, query } = props;
    const { t } = useTranslation();
    const absenceId = query.absence_id;
    const claim = appLogic.employers.claim;
    const user = appLogic.users.user;

    assert(appLogic.employers);
    // Since we are within a withUser higher order component, user should always be set
    assert(user);

    useEffect(() => {
      if (!claim) {
        appLogic.employers.loadClaim(absenceId);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [claim]);

    useEffect(() => {
      if (
        isFeatureEnabled("employerShowVerifications") &&
        claim &&
        user.hasUnverifiedEmployer
      ) {
        const employer = user.user_leave_administrators.find(
          (employer) =>
            !employer.verified && claim.employer_id === employer.employer_id
        );
        if (employer && employer.employer_id) {
          appLogic.portalFlow.goTo(routes.employers.verifyContributions, {
            employer_id: employer.employer_id,
            next: appLogic.portalFlow.pathWithParams,
          });
        }
      }
    }, [appLogic.portalFlow, claim, user]);

    if (!claim) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner
            aria-valuetext={t("components.withEmployerClaim.loadingLabel")}
          />
        </div>
      );
    }

    return <Component {...props} claim={claim} />;
  };

  ComponentWithClaim.propTypes = {
    appLogic: PropTypes.shape({
      appErrors: PropTypes.object.isRequired,
      employers: PropTypes.shape({
        claim: PropTypes.instanceOf(EmployerClaim),
        loadClaim: PropTypes.func.isRequired,
      }).isRequired,
      portalFlow: PropTypes.shape({
        goTo: PropTypes.func.isRequired,
        pathname: PropTypes.string.isRequired,
        pathWithParams: PropTypes.string,
      }),
      users: PropTypes.shape({
        user: PropTypes.instanceOf(User).isRequired,
      }).isRequired,
    }).isRequired,
    query: PropTypes.shape({
      absence_id: PropTypes.string.isRequired,
    }),
  };

  return withUser(ComponentWithClaim);
};

export default withEmployerClaim;
