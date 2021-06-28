import React, { useEffect } from "react";
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
 * @returns {React.Component} - Component with claims prop
 */
const withClaims = (Component) => {
  const ComponentWithClaims = (props) => {
    const { appLogic, query } = props;
    const { t } = useTranslation();

    assert(appLogic.claims);
    // Since we are within a withUser higher order component, user should always be set
    assert(appLogic.users.user);

    const { isLoadingClaims } = appLogic.claims;
    const requestedPageOffset = query.page_offset;
    const requestedFilters = {};
    if (query.claim_status) requestedFilters.claim_status = query.claim_status;
    if (query.employer_id) requestedFilters.employer_id = query.employer_id;

    useEffect(() => {
      appLogic.claims.loadPage(requestedPageOffset, requestedFilters);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isLoadingClaims, requestedPageOffset, Object.values(requestedFilters)]);

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
        activeFilters={appLogic.claims.activeFilters}
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
    query: PropTypes.shape({
      claim_status: PropTypes.string,
      employer_id: PropTypes.string,
      page_offset: PropTypes.string,
    }),
  };

  return withUser(ComponentWithClaims);
};

export default withClaims;
