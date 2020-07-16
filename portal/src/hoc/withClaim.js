import React, { useEffect } from "react";
import PropTypes from "prop-types";
import Spinner from "../components/Spinner";

/**
 * Higher order component that *MUST* be a child of App
 * and expects a Collection of claims as a prop
 * Adds a single claim to a component based on query parameters
 * @param {React.Component} Component - Component to receive claim prop
 * @returns {React.Component} - Component with claim prop
 */
const withClaim = (Component) => {
  const ComponentWithClaim = (props) => {
    const { query, appLogic } = props;

    useEffect(() => {
      appLogic.loadClaims();
    });

    const claim = appLogic.claims ? appLogic.claims.get(query.claim_id) : null;

    if (!claim) return <Spinner aria-valuetext="Loading claims" />;

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
