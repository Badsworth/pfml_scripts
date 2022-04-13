import ChangeRequest, {
  ChangeRequestType,
} from "../../../models/ChangeRequest";

import withChangeRequest, {
  WithChangeRequestProps,
} from "src/hoc/withChangeRequest";
import Alert from "../../../components/core/Alert";
import ClaimDetail from "../../../models/ClaimDetail";
import Heading from "src/components/core/Heading";
import LeaveReason from "../../../models/LeaveReason";
import PageNotFound from "../../../components/PageNotFound";
import QuestionPage from "../../../components/QuestionPage";
import React from "react";
import ReviewRow from "src/components/ReviewRow";
import { Trans } from "react-i18next";
import findKeyByValue from "../../../utils/findKeyByValue";
import formatDate from "src/utils/formatDate";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "src/routes";
import { useTranslation } from "../../../locales/i18n";

interface ChangeRequestTypeReviewProps {
  change_request?: ChangeRequest;
  claim_detail?: ClaimDetail;
}

const CancelationReview = () => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <Alert state="warning">
        {
          <Trans
            i18nKey="pages.claimsModifyReview.cancelationAlert"
            components={{
              "overpayments-link": (
                <a
                  href={routes.external.massgov.overpayments}
                  target="_blank"
                  rel="noreferrer"
                />
              ),
            }}
          />
        }
      </Alert>
      <Heading level="2">
        {t("pages.claimsModifyReview.cancelationHeading")}
      </Heading>
      <p>{t("pages.claimsModifyReview.cancelationBody")}</p>
    </React.Fragment>
  );
};

const WithdrawalReview = () => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <Heading level="2">
        {t("pages.claimsModifyReview.withdrawalHeading")}
      </Heading>
      <p>{t("pages.claimsModifyReview.withdrawalBody")}</p>
    </React.Fragment>
  );
};

const ModificationReview = (props: ChangeRequestTypeReviewProps) => {
  const { t } = useTranslation();
  const { change_request, claim_detail } = props;

  // TODO (PORTAL-2031): Remove when attached to HOC
  if (!change_request || !claim_detail) return null;

  const context = change_request.isExtension(claim_detail.endDate)
    ? "extension"
    : "endingEarly";

  return (
    <React.Fragment>
      <Heading level="2">
        {t("pages.claimsModifyReview.modificationHeading")}
      </Heading>
      <p>{t("pages.claimsModifyReview.modificationBody", { context })}</p>
      <ReviewRow
        noBorder
        level="3"
        label={t("pages.claimsModifyReview.modificationReviewRowLabel")}
      >
        {t("pages.claimsModifyReview.modificationReviewRowValue", {
          startDate: formatDate(change_request.start_date).short(),
          endDate: formatDate(change_request.end_date).short(),
        })}
      </ReviewRow>
    </React.Fragment>
  );
};

const MedicalToBondingReview = (props: ChangeRequestTypeReviewProps) => {
  const { t } = useTranslation();
  const { change_request, claim_detail } = props;
  // TODO (PORTAL-2031): Remove when attached to HOC
  if (!change_request || !claim_detail) return null;

  const pregnancyOnlyClaimDetail = new ClaimDetail({
    ...claim_detail,
    absence_periods: claim_detail.absence_periods.filter((period) => {
      return (
        period.reason === LeaveReason.pregnancy ||
        (period.reason === LeaveReason.medical &&
          ["Prenatal Disability", "Prenatal Care"].includes(
            period.reason_qualifier_one
          ))
      );
    }),
  });
  const context = !!change_request.document_submitted_at
    ? "hasProof"
    : "doesNotHaveProof";

  return (
    <React.Fragment>
      <Heading level="2">
        {t("pages.claimsModifyReview.medicalToBondingHeading")}
      </Heading>
      <p>{t("pages.claimsModifyReview.medicalToBondingBody1")}</p>
      <p>{t("pages.claimsModifyReview.medicalToBondingBody2", { context })}</p>
      <ReviewRow
        noBorder
        level="3"
        label={t("pages.claimsModifyReview.medicalReviewRowLabel")}
      >
        <Trans
          i18nKey="pages.claimsModifyReview.medicalReviewRowValue"
          values={{
            startDate: formatDate(pregnancyOnlyClaimDetail.startDate).short(),
            endDate: formatDate(pregnancyOnlyClaimDetail.endDate).short(),
          }}
        />
      </ReviewRow>
      <ReviewRow
        noBorder
        level="3"
        label={t("pages.claimsModifyReview.bondingReviewRowLabel")}
      >
        <Trans
          i18nKey="pages.claimsModifyReview.bondingReviewRowValue"
          values={{
            startDate: formatDate(change_request?.start_date).short(),
            endDate: formatDate(change_request?.end_date).short(),
          }}
        />
      </ReviewRow>
    </React.Fragment>
  );
};

export const Review = (
  props: WithChangeRequestProps & { claim_detail?: ClaimDetail }
) => {
  // TODO (PORTAL-2031): Remove when attached to HOC
  const change_request = props.change_request;
  const claim_detail = props.claim_detail || new ClaimDetail({});

  const { t } = useTranslation();

  const changeRequestTypeContext = findKeyByValue(
    ChangeRequestType,
    change_request.change_request_type
  );
  const buttonText = t("pages.claimsModifyReview.buttonText", {
    context: changeRequestTypeContext,
  });

  /* eslint-disable require-await */
  const handleSubmit = async () => {
    // Do nothing for now
  };

  // TODO(PORTAL-2064): Remove claimantShowModifications feature flag
  if (!isFeatureEnabled("claimantShowModifications")) return <PageNotFound />;

  return (
    <QuestionPage
      title={t("pages.claimsModifyReview.title")}
      onSave={handleSubmit}
      continueButtonLabel={buttonText}
    >
      {changeRequestTypeContext === "medicalToBonding" && (
        <MedicalToBondingReview
          claim_detail={claim_detail}
          change_request={change_request}
        />
      )}
      {changeRequestTypeContext === "withdrawal" &&
        claim_detail.hasApprovedStatus && <CancelationReview />}
      {changeRequestTypeContext === "withdrawal" &&
        !claim_detail.hasApprovedStatus &&
        claim_detail.hasPendingStatus && <WithdrawalReview />}
      {changeRequestTypeContext === "modification" && (
        <ModificationReview
          claim_detail={claim_detail}
          change_request={change_request}
        />
      )}
    </QuestionPage>
  );
};

export default withChangeRequest(Review);
