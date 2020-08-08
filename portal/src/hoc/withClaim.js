import React, { useEffect } from "react";
import PropTypes from "prop-types";
import Spinner from "../components/Spinner";
import { useTranslation } from "../locales/i18n";

/**
 * Higher order component that *MUST* be a child of App
 * and expects a Collection of claims as a prop
 * Adds a single claim to a component based on query parameters
 * @param {React.Component} Component - Component to receive claim prop
 * @returns {React.Component} - Component with claim prop
 */
const withClaim = (Component) => {
  const ComponentWithClaim = (props) => {
    const { t } = useTranslation();
    const { query, appLogic } = props;

    useEffect(() => {
      appLogic.claims.load();
    });

    const claim = appLogic.claims.claims
      ? appLogic.claims.claims.get(query.claim_id)
      : null;

    if (!claim)
      return (
        <div className="margin-top-8 text-center">
          <Spinner aria-valuetext={t("components.spinner.label")} />
        </div>
      );

    return <Component {...props} claim={claim} />;
  };

  ComponentWithClaim.propTypes = {
    query: PropTypes.shape({
      claim_id: PropTypes.string,
    }).isRequired,
    appLogic: PropTypes.object.isRequired,
  };

  return ComponentWithClaim;
};

export default withClaim;
