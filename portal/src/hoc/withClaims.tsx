import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";
import ClaimCollection from "../models/ClaimCollection";
import PaginationMeta from "../models/PaginationMeta";
import Spinner from "../components/core/Spinner";
import { omitBy } from "lodash";
import { useTranslation } from "../locales/i18n";

export interface ApiParams {
  page_offset?: string;
  employer_id?: string;
  search?: string;
  claim_status?: string;
  order_by?: "absence_status" | "created_at" | "employee";
  order_direction?: "ascending" | "descending";
}

export interface WithClaimsProps extends WithUserProps {
  claims: ClaimCollection;
  paginationMeta: PaginationMeta;
}

/**
 * Higher order component that provides the current user's claims to the wrapped component.
 * The higher order component also loads the claims if they have not already been loaded.
 */
function withClaims<T extends WithClaimsProps>(
  Component: React.ComponentType<T>,
  apiParams: ApiParams = {}
) {
  const ComponentWithClaims = (props: Omit<T, "claims" | "paginationMeta">) => {
    const { appLogic } = props;
    const { page_offset } = apiParams;
    const { t } = useTranslation();

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
      (value) => value === null || value === undefined
    );
    const filters = omitBy(
      {
        claim_status: apiParams.claim_status,
        employer_id: apiParams.employer_id,
        search: apiParams.search,
      },
      (value) => value === null || value === undefined
    );

    useEffect(() => {
      appLogic.claims.loadPage(page_offset, order, filters);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isLoadingClaims, page_offset, order, filters]);

    if (isLoadingClaims) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner aria-label={t("components.withClaims.loadingLabel")} />
        </div>
      );
    }

    return (
      <Component
        {...(props as T)}
        claims={appLogic.claims.claims}
        paginationMeta={appLogic.claims.paginationMeta}
      />
    );
  };

  return withUser(ComponentWithClaims);
}

export default withClaims;
