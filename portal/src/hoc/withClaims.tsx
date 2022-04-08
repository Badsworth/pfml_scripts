import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";
import ApiResourceCollection from "../models/ApiResourceCollection";
import Claim from "../models/Claim";
import { GetClaimsParams } from "../api/ClaimsApi";
import PaginationMeta from "../models/PaginationMeta";
import Spinner from "../components/core/Spinner";
import { omitBy } from "lodash";
import { useTranslation } from "../locales/i18n";

export interface WithClaimsProps extends WithUserProps {
  claims: ApiResourceCollection<Claim>;
  paginationMeta: PaginationMeta;
}

/**
 * Higher order component that provides the current user's claims to the wrapped component.
 * The higher order component also loads the claims if they have not already been loaded.
 */
function withClaims<T extends WithClaimsProps>(
  Component: React.ComponentType<T>,
  apiParams: GetClaimsParams = {}
) {
  const ComponentWithClaims = (props: Omit<T, "claims" | "paginationMeta">) => {
    const { appLogic } = props;
    const { t } = useTranslation();

    const { isLoadingClaims } = appLogic.claims;

    // Exclude null or undefined values since we don't want to
    // send those into the API request's query string, and our
    // UI components won't need to filter them out when determining
    // how many filters are active.
    const params = omitBy(
      {
        page_offset: apiParams.page_offset,
        order_by: apiParams.order_by,
        order_direction: apiParams.order_direction,
        is_reviewable: apiParams.is_reviewable,
        request_decision: apiParams.request_decision,
        employer_id: apiParams.employer_id,
        search: apiParams.search,
      },
      (value) => value === null || value === undefined
    );

    useEffect(() => {
      appLogic.claims.loadPage(params);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isLoadingClaims, params]);

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
