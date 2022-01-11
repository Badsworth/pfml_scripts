import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";

import BackButton from "../components/BackButton";
import PageNotFound from "../components/PageNotFound";
import Spinner from "../components/core/Spinner";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

export interface QueryProps {
  absence_case_id?: string;
  absence_id?: string;
  uploaded_document_type?: string;
}

export interface WithClaimDetailProps extends WithUserProps {
  activePath?: string;
  query: QueryProps;
}

/**
 * Higher order component that loads a claim detail if not yet loaded
 */
function withClaimDetail<T extends WithClaimDetailProps>(
  Component: React.ComponentType<T>
) {
  const ComponentWithClaimDetail = (props: WithClaimDetailProps) => {
    const { appLogic, query } = props;
    const { t } = useTranslation();
    const {
      claims: { claimDetail = {}, isLoadingClaimDetail, loadClaimDetail },
    } = appLogic;

    // Determine absence/application ids
    const { absence_case_id, absence_id } = query;
    const absenceId = absence_id || absence_case_id;

    // Load claim detail if absence id is valid
    useEffect(() => {
      if (absenceId) loadClaimDetail(absenceId);

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [absenceId]);

    /**
     * If there is no absence_id query parameter,
     * then return the PFML 404 page.
     */
    const isAbsenceCaseId = Boolean(absenceId?.length);
    if (!isAbsenceCaseId) return <PageNotFound />;

    if (isLoadingClaimDetail) {
      return (
        <div className="text-center">
          <Spinner
            aria-label={t("pages.claimsStatus.loadingClaimDetailLabel")}
          />
        </div>
      );
    }

    return <Component claimDetail={claimDetail} {...(props as T)} />;
  };

  return withUser(ComponentWithClaimDetail);
}

export default withClaimDetail;
