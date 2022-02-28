import React, { ReactChild, useEffect } from "react";
import BackButton from "src/components/BackButton";
import Spinner from "src/components/core/Spinner";
import withUser, { PageProps, WithUserProps } from "src/hoc/withUser";
import { AppLogic } from "../../hooks/useAppLogic";
import { t, useTranslation } from "src/locales/i18n";
import Payment from "src/models/Payment";
import routes from "src/routes";
import { paymentStatusViewHelper,showPaymentsTab} from "src/utils/paymentsHelpers"
import { BondingLeaveAlert } from "./BondingLeaveAlert";
import StatusNavigationTabs from "./StatusNavigationTabs";
import { ClaimsLogic } from "src/hooks/useClaimsLogic";
import useDocumentsLogic from "src/hooks/useDocumentsLogic";

interface StatusLayoutProps{
  appLogic: AppLogic;
  query: {
    absence_case_id: string;
    absence_id: string;
    uploaded_document_type: string;
  };
  children: React.ReactNode;
}

export const StatusLayout({
  appLogic,
  query,
  children
}: WithUserProps & StatusLayoutProps
) => {
    const { t } = useTranslation();
    const {
      claims: { claimDetail, loadClaimDetail, isLoadingClaimDetail },
      documents: {
        documents: allClaimDocuments,
        loadAll: loadAllClaimDocuments,
      },
      payments: { loadPayments, loadedPaymentsData },
    } = appLogic;
    const { absence_case_id, absence_id, uploaded_document_type } = query;
    const application_id = claimDetail?.application_id;

    const absenceId = absence_id || absence_case_id;

    useEffect(() => {
      if (absenceId) {
        loadClaimDetail(absenceId);
        loadPayments(absenceId);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [absenceId]);
  
    useEffect(() => {
      if (application_id) {
        loadAllClaimDocuments(application_id);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [application_id]);
  
      // Check both because claimDetail could be cached from a different status page.
  if (isLoadingClaimDetail || !claimDetail) {
    return (
      <div className="text-center">
        <Spinner aria-label={t("pages.claimsStatus.loadingClaimDetailLabel")} />
      </div>
    );
  }
  const helper = paymentStatusViewHelper(
    claimDetail,
    allClaimDocuments,
    loadedPaymentsData || new Payment()
  );

  // Determines if payment tab is displayed
  const isPaymentsTab = showPaymentsTab(helper);

  return (
    <React.Fragment>
      <BondingLeaveAlert claimDetail={claimDetail} allClaimDocuments={allClaimDocuments} loadedPaymentsData={loadedPaymentsData}/>
  <BackButton
    label={t("pages.claimsStatus.backButtonLabel")}
    href={routes.applications.index}
  />
  {isPaymentsTab && (
      <StatusNavigationTabs
        activePath={appLogic.portalFlow.pathname}
        absence_id={absenceId}
      />
    )}
      {children}
    </React.Fragment>
  )
}


export default withUser(StatusLayout);
