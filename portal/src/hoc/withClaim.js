import Collection from "../models/Collection";
import PropTypes from "prop-types";
import React from "react";

/**
 * Higher order component that *MUST* be a child of App
 * and expects a Collection of claims as a prop
 * Adds a single claim to a component based on query parameters
 * @param {React.Component} Component - Component to receive claim prop
 * @returns {React.Component} - Component with claim prop
 */
const withClaim = (Component) => {
  const componentWithClaim = (props) => {
    const { query, claims } = props;
    const claimId = query.claim_id;

    const claim = claims.get(claimId);

    return <Component {...props} claim={claim} />;
  };

  componentWithClaim.propTypes = {
    query: PropTypes.shape({
      claim_id: PropTypes.string,
    }).isRequired,
    claims: PropTypes.instanceOf(Collection).isRequired,
  };

  return componentWithClaim;
};

export default withClaim;
