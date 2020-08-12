import ClaimCollection from "../models/ClaimCollection";
import PropTypes from "prop-types";
import React from "react";
import assert from "assert";
import routes from "../routes";
import { useRouter } from "next/router";
import withClaims from "./withClaims";

/**
 * Higher order component that uses withClaims to load claims if they are not yet loaded
 * then adds a single claim to the wrapped component based on query parameters
 * @param {React.Component} Component - Component to receive claim prop
 * @returns {React.Component} - Component with claim prop
 */
const withClaim = (Component) => {
  const ComponentWithClaim = (props) => {
    const { claims, query } = props;
    const router = useRouter();

    assert(claims);
    const claim = claims.get(query.claim_id);

    if (!claim) {
      router.push(routes.applications);
      return null;
    } else {
      return <Component {...props} claim={claim} />;
    }
  };

  ComponentWithClaim.propTypes = {
    claims: PropTypes.instanceOf(ClaimCollection).isRequired,
    query: PropTypes.shape({
      claim_id: PropTypes.string.isRequired,
    }).isRequired,
  };

  return withClaims(ComponentWithClaim);
};

export default withClaim;
