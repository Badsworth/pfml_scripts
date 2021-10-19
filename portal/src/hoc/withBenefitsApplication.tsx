import React, { useEffect } from "react";
import BenefitsApplicationCollection from "../models/BenefitsApplicationCollection";
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
const withBenefitsApplication = (Component) => {
  const ComponentWithClaim = (props) => {
    const { appLogic, query } = props;
    const { t } = useTranslation();

    assert(appLogic.benefitsApplications);
    // Since we are within a withUser higher order component, user should always be set
    assert(appLogic.users.user);

    const application_id = query.claim_id;
    const benefitsApplications =
      appLogic.benefitsApplications.benefitsApplications;
    const claim = benefitsApplications.getItem(application_id);
    const shouldLoad =
      !appLogic.benefitsApplications.hasLoadedBenefitsApplicationAndWarnings(
        application_id
      );

    useEffect(() => {
      if (shouldLoad) {
        appLogic.benefitsApplications.load(application_id);
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

    return <Component {...props} claim={claim} />;
  };

  ComponentWithClaim.propTypes = {
    appLogic: PropTypes.shape({
      users: PropTypes.shape({
        user: PropTypes.instanceOf(User).isRequired,
      }).isRequired,
      benefitsApplications: PropTypes.shape({
        benefitsApplications: PropTypes.instanceOf(
          BenefitsApplicationCollection
        ),
        load: PropTypes.func.isRequired,
        hasLoadedBenefitsApplicationAndWarnings: PropTypes.func.isRequired,
      }).isRequired,
      appErrors: PropTypes.object.isRequired,
    }).isRequired,
    query: PropTypes.shape({
      claim_id: PropTypes.string.isRequired,
    }).isRequired,
  };

  return withUser(ComponentWithClaim);
};

export default withBenefitsApplication;
