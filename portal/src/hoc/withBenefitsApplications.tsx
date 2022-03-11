import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";
import ApiResourceCollection from "../models/ApiResourceCollection";
import BenefitsApplication from "../models/BenefitsApplication";
import PaginationMeta from "src/models/PaginationMeta";
import Spinner from "../components/core/Spinner";
import { useTranslation } from "../locales/i18n";

export interface ApiParams {
  page_offset?: string;
}
export interface WithBenefitsApplicationsProps extends WithUserProps {
  claims: ApiResourceCollection<BenefitsApplication>;
  paginationMeta: PaginationMeta;
}

/**
 * Higher order component that provides the current user's claims to the wrapped component.
 * The higher order component also loads the claims if they have not already been loaded.
 */
function withBenefitsApplications<T extends WithBenefitsApplicationsProps>(
  Component: React.ComponentType<T>,
  apiParams: ApiParams = {}
) {
  const ComponentWithClaims = (props: WithUserProps) => {
    const { appLogic } = props;
    const { page_offset } = apiParams;
    const { t } = useTranslation();

    const { benefitsApplications, paginationMeta, isLoadingClaims } =
      appLogic.benefitsApplications;

    useEffect(() => {
      appLogic.benefitsApplications.loadPage(page_offset);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isLoadingClaims, page_offset]);

    if (isLoadingClaims) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner
            aria-label={t("components.withBenefitsApplications.loadingLabel")}
          />
        </div>
      );
    }
    return (
      <Component
        {...(props as T)}
        claims={benefitsApplications}
        paginationMeta={paginationMeta}
      />
    );
  };
  return withUser(ComponentWithClaims);
}

export default withBenefitsApplications;
