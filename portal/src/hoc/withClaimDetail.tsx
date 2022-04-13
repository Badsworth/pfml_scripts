import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";
import ClaimDetail from "../models/ClaimDetail";
import PageNotFound from "src/components/PageNotFound";
import Spinner from "../components/core/Spinner";
import { useTranslation } from "../locales/i18n";

export interface WithClaimDetailProps extends WithUserProps {
  claim_detail: ClaimDetail;
}

interface QueryProps {
  query: {
    absence_id?: string;
    absence_case_id?: string;
  };
}

function withClaimDetail<T extends WithClaimDetailProps>(
  Component: React.ComponentType<T>
) {
  const ComponentWithClaimDetail = (props: T & QueryProps) => {
    const { appLogic } = props;
    const { t } = useTranslation();

    const { claimDetail, loadClaimDetail, isLoadingClaimDetail } =
      appLogic.claims;
    const { absence_case_id, absence_id } = props.query;
    const absenceId = absence_id || absence_case_id;

    useEffect(() => {
      if (absenceId) {
        loadClaimDetail(absenceId);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [absenceId]);

    if (!absenceId) return <PageNotFound />;

    // Check both because claimDetail could be cached from a different status page.
    if (isLoadingClaimDetail || !claimDetail) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner aria-label={t("components.withClaims.loadingLabel")} />
        </div>
      );
    }

    return <Component {...(props as T)} claim_detail={claimDetail} />;
  };

  return withUser(ComponentWithClaimDetail);
}

export default withClaimDetail;
