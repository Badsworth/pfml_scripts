import React, { useEffect } from "react";
import EmployerClaim from "../models/EmployerClaim";
import PropTypes from "prop-types";
import { Spinner } from "../components/Spinner";
import User from "../models/User";
import assert from "assert";
import { useTranslation } from "react-i18next";
import withUser from "./withUser";

/**
 * Higher order component that loads a claim if not yet loaded,
 * then adds a single claim to the wrapper component based on query parameters.
 * This should be used in routes meant for employers.
 * @param {React.Component} Component - Component to receive claim prop
 * @returns {React.Component} component with claim prop
 */
const withEmployerClaim = (Component) => {
  const ComponentWithClaim = (props) => {
    const { appLogic, query } = props;
    const { t } = useTranslation();

    assert(appLogic.employers);
    // Since we are within a withUser higher order component, user should always be set
    assert(appLogic.users.user);

    const absenceId = query.absence_id;
    const claim = appLogic.employers.claim;

    useEffect(() => {
      if (!claim) {
        appLogic.employers.load(absenceId);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [claim]);

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
        load: PropTypes.func.isRequired,
      }).isRequired,
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
