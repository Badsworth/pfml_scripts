import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";

import BackButton from "../components/BackButton";
import PageNotFound from "../components/PageNotFound";
import Spinner from "../components/core/Spinner";
import hasDocumentsLoadError from "../utils/hasDocumentsLoadError";
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
      claims: { claimDetail, isLoadingClaimDetail, loadClaimDetail },
      documents: { hasLoadedClaimDocuments, loadAll },
    } = appLogic;

    // Determine absence/application ids
    const { absence_case_id, absence_id } = query;
    const application_id = claimDetail?.application_id || "";
    const absenceId = absence_id || absence_case_id;

    // Check for documents and related errors
    const hasDocuments = hasLoadedClaimDocuments(application_id);
    const hasDocumentsError = hasDocumentsLoadError(
      appLogic.appErrors,
      application_id
    );

    // Load claim detail if absence id is valid
    useEffect(() => {
      if (absenceId) loadClaimDetail(absenceId);

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [absenceId]);

    // Load claim documents if application id is valid
    useEffect(() => {
      if (application_id) loadAll(application_id, true);

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [application_id, appLogic.portalFlow.pathname]);

    // Address potential hash values in URL
    useEffect(() => {
      /**
       * If URL includes a location.hash then page
       * should scroll into view on that id tag,
       * provided the id tag exists.
       */
      if (location.hash) {
        const anchorId = document.getElementById(location.hash.substring(1));
        if (anchorId) anchorId.scrollIntoView();
      }
    }, [hasDocuments, hasDocumentsError, isLoadingClaimDetail]);

    /**
     * If there is no absence_id query parameter,
     * then return the PFML 404 page.
     */
    const isAbsenceCaseId = Boolean(absenceId?.length);
    if (!isAbsenceCaseId) return <PageNotFound />;

    // only hide page content if there is an error that's not DocumentsLoadError.
    const hasNonDocumentsLoadError: boolean = appLogic.appErrors.items.some(
      (error) => error.name !== "DocumentsLoadError"
    );

    if (hasNonDocumentsLoadError) {
      return (
        <BackButton
          label={t("pages.claimsStatus.backButtonLabel")}
          href={routes.applications.index}
        />
      );
    }

    // Check both because claimDetail could be cached from a different status page.
    if (isLoadingClaimDetail || !claimDetail) {
      return (
        <div className="text-center">
          <Spinner
            aria-label={t("pages.claimsStatus.loadingClaimDetailLabel")}
          />
        </div>
      );
    }

    return <Component {...(props as T)} />;
  };

  return withUser(ComponentWithClaimDetail);
}

export default withClaimDetail;
