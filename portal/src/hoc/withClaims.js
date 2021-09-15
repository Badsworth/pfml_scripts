import React, { useEffect } from "react";
import { isNil, omitBy } from "lodash";
import ClaimCollection from "../models/ClaimCollection";
import PaginationMeta from "../models/PaginationMeta";
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
 * @param {object} apiParams
 * @param {string} [apiParams.claim_status]
 * @param {string} [apiParams.employer_id]
 * @param {string} [apiParams.order_by]
 * @param {string} [apiParams.order_direction]
 * @param {string} [apiParams.page_offset]
 * @param {string} [apiParams.search]
 * @returns {React.Component} - Component with claims prop
 */
const withClaims = (Component, apiParams = {}) => {
  const ComponentWithClaims = (props) => {
    const { appLogic } = props;
    const { page_offset } = apiParams;
    const { t } = useTranslation();

    assert(appLogic.claims);
    // Since we are within a withUser higher order component, user should always be set
    assert(appLogic.users.user);

    const { isLoadingClaims } = appLogic.claims;

    // Exclude null or undefined values since we don't want to
    // send those into the API request's query string, and our
    // UI components won't need to filter them out when determining
    // how many filters are active.
    const order = omitBy(
      {
        order_by: apiParams.order_by,
        order_direction: apiParams.order_direction,
      },
      isNil
    );
    const filters = omitBy(
      {
        claim_status: apiParams.claim_status,
        employer_id: apiParams.employer_id,
        search: apiParams.search,
      },
      isNil
    );

    useEffect(() => {
      appLogic.claims.loadPage(page_offset, order, filters);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isLoadingClaims, page_offset, order, filters]);

    if (isLoadingClaims) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner aria-valuetext={t("components.withClaims.loadingLabel")} />
        </div>
      );
    }

    return (
      <Component
        {...props}
        claims={appLogic.claims.claims}
        paginationMeta={appLogic.claims.paginationMeta}
      />
    );
  };

  ComponentWithClaims.propTypes = {
    appLogic: PropTypes.shape({
      users: PropTypes.shape({
        user: PropTypes.instanceOf(User).isRequired,
      }).isRequired,
      claims: PropTypes.shape({
        activeFilters: PropTypes.shape({
          employer_id: PropTypes.string,
        }).isRequired,
        claims: PropTypes.instanceOf(ClaimCollection),
        isLoadingClaims: PropTypes.bool,
        loadPage: PropTypes.func.isRequired,
        paginationMeta: PropTypes.instanceOf(PaginationMeta),
      }).isRequired,
    }).isRequired,
  };

  return withUser(ComponentWithClaims);
};

export default withClaims;
