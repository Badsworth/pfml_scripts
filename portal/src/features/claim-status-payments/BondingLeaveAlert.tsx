import {
  getInfoAlertContext,
  paymentStatusViewHelper,
} from "src/utils/paymentsHelpers";
import Alert from "src/components/core/Alert";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { BenefitsApplicationDocument } from "src/models/Document";
import ClaimDetail from "src/models/ClaimDetail";
import { Payment } from "src/models/Payment";
import React from "react";
import { Trans } from "react-i18next";
import routes from "src/routes";
import { t } from "src/locales/i18n";

interface BondingLeaveAlertProps {
  allClaimDocuments: ApiResourceCollection<BenefitsApplicationDocument>;
  claimDetail: ClaimDetail;
  loadedPaymentsData: Payment;
}

export const BondingLeaveAlert = ({
  claimDetail,
  allClaimDocuments,
  loadedPaymentsData,
}: BondingLeaveAlertProps) => {
  const helper = paymentStatusViewHelper(
    claimDetail,
    allClaimDocuments,
    // eslint-disable-next-line @typescript-eslint/strict-boolean-expressions
    loadedPaymentsData || new Payment()
  );

  const {
    hasApprovedStatus,
    hasPendingStatus,
    hasInReviewStatus,
    hasProjectedStatus,
  } = helper;
  // Determines if payment tab is displayed

  const infoAlertContext = getInfoAlertContext(helper);
  const displayAlert =
    !!infoAlertContext &&
    (hasPendingStatus ||
      hasApprovedStatus ||
      hasInReviewStatus ||
      hasProjectedStatus);
  return (
    <React.Fragment>
      {displayAlert && (
        <Alert
          className="margin-bottom-3"
          data-test="info-alert"
          heading={t("pages.claimsStatus.infoAlertHeading", {
            context: infoAlertContext,
          })}
          headingLevel="2"
          headingSize="4"
          noIcon
          state="info"
        >
          <p>
            <Trans
              i18nKey="pages.claimsStatus.infoAlertBody"
              tOptions={{ context: infoAlertContext }}
              components={{
                "about-bonding-leave-link": (
                  <a
                    href={
                      routes.external.massgov.benefitsGuide_aboutBondingLeave
                    }
                    target="_blank"
                    rel="noreferrer noopener"
                  />
                ),
                "contact-center-phone-link": (
                  <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                ),
              }}
            />
          </p>
        </Alert>
      )}
    </React.Fragment>
  );
};
