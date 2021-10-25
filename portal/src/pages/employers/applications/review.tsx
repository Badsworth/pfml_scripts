import PreviousLeave, {
  PreviousLeaveType,
} from "../../../models/PreviousLeave";
import React, { useEffect, useState } from "react";
import { get, isEqual, isNil, omit } from "lodash";
import Alert from "../../../components/Alert";
import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/Button";
import ConcurrentLeave from "../../../components/employers/ConcurrentLeave";
import ConcurrentLeaveModel from "../../../models/ConcurrentLeave";
import { DocumentType } from "../../../models/Document";
import EmployeeInformation from "../../../components/employers/EmployeeInformation";
import EmployeeNotice from "../../../components/employers/EmployeeNotice";
import EmployerBenefit from "../../../models/EmployerBenefit";
import EmployerBenefits from "../../../components/employers/EmployerBenefits";
import EmployerClaim from "../../../models/EmployerClaim";
import EmployerDecision from "../../../components/employers/EmployerDecision";
import Feedback from "../../../components/employers/Feedback";
import FraudReport from "../../../components/employers/FraudReport";
import Heading from "../../../components/Heading";
import LeaveDetails from "../../../components/employers/LeaveDetails";
import LeaveReason from "../../../models/LeaveReason";
import LeaveSchedule from "../../../components/employers/LeaveSchedule";
import PreviousLeaves from "../../../components/employers/PreviousLeaves";
import ReviewHeading from "../../../components/ReviewHeading";
import ReviewRow from "../../../components/ReviewRow";
import SupportingWorkDetails from "../../../components/employers/SupportingWorkDetails";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import findDocumentsByTypes from "../../../utils/findDocumentsByTypes";
import formatDateRange from "../../../utils/formatDateRange";
import leaveReasonToPreviousLeaveReason from "../../../utils/leaveReasonToPreviousLeaveReason";
import routes from "../../../routes";
import updateAmendments from "../../../utils/updateAmendments";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../../hooks/useThrottledHandler";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

interface ReviewProps {
  appLogic: AppLogic;
  claim: EmployerClaim;
  query: {
    absence_id: string;
  };
}

export const Review = (props: ReviewProps) => {
  const {
    appLogic,
    claim,
    query: { absence_id: absenceId },
  } = props;
  const {
    appErrors,
    employers: { documents, downloadDocument, loadDocuments },
  } = appLogic;
  const { t } = useTranslation();

  const shouldShowV2 = !!claim.uses_second_eform_version;
  // explicitly check for false as opposed to falsy values.
  // temporarily allows the redirect behavior to work even
  // if the API has not been updated to populate the field.
  if (claim.is_reviewable === false) {
    appLogic.portalFlow.goTo(routes.employers.status, {
      absence_id: absenceId,
    });
  }

  // Generate id based on index for employer benefit and previous leave (id is not provided by API)
  // Note: these indices are used to properly display inline errors and amend employer benefits and
  // previous leaves. If employer_benefit_id and previous_leave_id no longer match the indices, then
  // the functionality described above will need to be reimplemented.
  const indexedEmployerBenefits = claim.employer_benefits.map(
    (benefit, index) =>
      new EmployerBenefit({ ...benefit, employer_benefit_id: index.toString() })
  );
  const indexedPreviousLeaves = claim.previous_leaves.map(
    (leave, index) =>
      new PreviousLeave({ ...leave, previous_leave_id: index.toString() })
  );

  const { clearField, getField, formState, updateFields } = useFormState({
    // base fields
    concurrentLeave: claim.concurrent_leave,
    amendedConcurrentLeave: claim.concurrent_leave,
    employerBenefits: indexedEmployerBenefits,
    amendedBenefits: indexedEmployerBenefits,
    previousLeaves: indexedPreviousLeaves,
    amendedPreviousLeaves: indexedPreviousLeaves,
    hours_worked_per_week: claim.hours_worked_per_week,
    comment: "",
    employer_decision: "Approve",
    fraud: undefined,
    employee_notice: undefined,
    believeRelationshipAccurate: undefined,
    relationshipInaccurateReason: "",
    should_show_comment_box: false,
    // added fields
    addedBenefits: [],
    addedPreviousLeaves: [],
    addedConcurrentLeave: null,
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const [allPreviousLeaves, setAllPreviousLeaves] = useState<PreviousLeave[]>(
    []
  );
  useEffect(() => {
    setAllPreviousLeaves([
      ...formState.amendedPreviousLeaves,
      ...formState.addedPreviousLeaves,
    ]);
  }, [formState.amendedPreviousLeaves, formState.addedPreviousLeaves]);

  const [allEmployerBenefits, setAllEmployerBenefits] = useState<
    EmployerBenefit[]
  >([]);
  useEffect(() => {
    setAllEmployerBenefits([
      ...formState.amendedBenefits,
      ...formState.addedBenefits,
    ]);
  }, [formState.amendedBenefits, formState.addedBenefits]);

  const isReportingFraud = formState.fraud === "Yes";
  const isDenyingRequest = formState.employer_decision === "Deny";
  const isEmployeeNoticeInsufficient = formState.employee_notice === "No";
  const shouldShowCommentBox = formState.should_show_comment_box;

  const isCommentRequired =
    isReportingFraud ||
    isDenyingRequest ||
    isEmployeeNoticeInsufficient ||
    shouldShowCommentBox;

  useEffect(() => {
    updateFields({
      should_show_comment_box:
        isDenyingRequest || isEmployeeNoticeInsufficient || !!formState.comment,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDenyingRequest, isEmployeeNoticeInsufficient]);

  useEffect(() => {
    if (!shouldShowCommentBox) {
      updateFields({ comment: "" });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldShowCommentBox]);

  /**
   * Returns the context for the proper help message when the comment box is shown.
   */
  const buildFeedbackContext = () => {
    if (isReportingFraud) return "fraud";
    if (!isReportingFraud && isDenyingRequest) return "employerDecision";
    if (!isDenyingRequest && isEmployeeNoticeInsufficient)
      return "employeeNotice";

    return "";
  };

  const isSubmitDisabled =
    (isCommentRequired && !formState.comment) ||
    (formState.believeRelationshipAccurate === "No" &&
      formState.relationshipInaccurateReason === "");
  const isCaringLeave = get(claim, "leave_details.reason") === LeaveReason.care;

  useEffect(() => {
    if (!documents) {
      loadDocuments(absenceId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documents, absenceId]);

  // only cert forms should be shown
  const allDocuments = documents ? documents.items : [];

  // TODO (CP-1983): Remove caring leave feature flag check
  // after turning on caring leave feature flag, use `findDocumentsByLeaveReason`
  // instead of `findDocumentsByTypes`
  const leaveReason = get(claim, "leave_details.reason");
  const certificationDocuments = findDocumentsByTypes(allDocuments, [
    DocumentType.certification[leaveReason],
    DocumentType.certification.medicalCertification,
  ]);

  const handleBenefitInputAdd = () => {
    updateFields({
      addedBenefits: [
        ...formState.addedBenefits,
        new EmployerBenefit({
          employer_benefit_id: allEmployerBenefits.length.toString(),
        }),
      ],
    });
  };

  const handleBenefitRemove = (benefitToRemove) => {
    const updatedAddedBenefits = formState.addedBenefits
      // remove selected benefit
      .filter(
        ({ employer_benefit_id }) =>
          employer_benefit_id !== benefitToRemove.employer_benefit_id
      )
      // reassign employer_benefit_id to keep indices accurate
      .map(
        (addedBenefit, index) =>
          new EmployerBenefit({ ...addedBenefit, employer_benefit_id: index })
      );
    updateFields({ addedBenefits: updatedAddedBenefits });
  };

  const handleBenefitInputChange = (
    updatedBenefit,
    formStateField = "amendedBenefits"
  ) => {
    const updatedBenefits = updateAmendments(
      get(formState, formStateField),
      updatedBenefit
    );
    updateFields({ [formStateField]: updatedBenefits });
  };

  const handlePreviousLeaveAdd = () => {
    updateFields({
      addedPreviousLeaves: [
        ...formState.addedPreviousLeaves,
        new PreviousLeave({
          is_for_current_employer: true,
          previous_leave_id: allPreviousLeaves.length.toString(),
        }),
      ],
    });
  };

  const handlePreviousLeaveRemove = (leaveToRemove) => {
    const updatedAddedLeaves = formState.addedPreviousLeaves
      // remove selected leave
      .filter(
        ({ previous_leave_id }) =>
          previous_leave_id !== leaveToRemove.previous_leave_id
      )
      // reassign previous_leave_id to keep indices accurate
      .map(
        (addedLeave, index) =>
          new PreviousLeave({ ...addedLeave, previous_leave_id: index })
      );
    updateFields({ addedPreviousLeaves: updatedAddedLeaves });
  };

  const handlePreviousLeavesChange = (
    updatedLeave,
    formStateField = "amendedPreviousLeaves"
  ) => {
    const originalPreviousLeave = get(
      formState,
      `previousLeaves.[${updatedLeave.previous_leave_id}]`
    );

    if (updatedLeave.type === PreviousLeaveType.sameReason) {
      updatedLeave.leave_reason = leaveReasonToPreviousLeaveReason(
        claim.leave_details.reason
      );
    } else if (
      updatedLeave.type === PreviousLeaveType.otherReason &&
      // leave admin did not cancel amendment.
      !isEqual(updatedLeave, originalPreviousLeave)
    ) {
      updatedLeave.leave_reason = undefined;
    }
    // don't revert previous leave reason if the amendment is canceled
    const updatedPreviousLeaves = updateAmendments(
      get(formState, formStateField),
      updatedLeave
    );
    updateFields({ [formStateField]: updatedPreviousLeaves });
  };

  const handleConcurrentLeaveAdd = () => {
    updateFields({
      addedConcurrentLeave: new ConcurrentLeaveModel({
        is_for_current_employer: true,
      }),
    });
  };

  const handleConcurrentLeaveRemove = () => {
    updateFields({ addedConcurrentLeave: null });
  };

  const handleConcurrentLeaveInputChange = (
    updatedLeave,
    formStateField = "amendedConcurrentLeave"
  ) => {
    updateFields({
      [formStateField]: {
        ...get(formState, formStateField),
        ...updatedLeave,
      },
    });
  };

  const handleBelieveRelationshipAccurateChange = (
    updatedBelieveRelationshipAccurate
  ) => {
    updateFields({
      believeRelationshipAccurate: updatedBelieveRelationshipAccurate,
    });
  };

  const handleRelationshipInaccurateReason = (
    updatedRelationshipInaccurateReason
  ) => {
    updateFields({
      relationshipInaccurateReason: updatedRelationshipInaccurateReason,
    });
  };

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();

    const concurrent_leave =
      formState.amendedConcurrentLeave || formState.addedConcurrentLeave;
    const employer_benefits = allEmployerBenefits.map((benefit) =>
      omit(benefit, ["employer_benefit_id"])
    );
    const previous_leaves = allPreviousLeaves.map((leave) =>
      omit(leave, ["previous_leave_id"])
    );

    // canceling amendments causes their values in formState to be null.
    // in these cases, we want to restore the claimant-provided, original values.
    const hours_worked_per_week = isNil(formState.hours_worked_per_week)
      ? claim.hours_worked_per_week
      : formState.hours_worked_per_week;

    const payload = {
      believe_relationship_accurate: undefined,
      comment: formState.comment || "",
      concurrent_leave,
      employer_benefits,
      employer_decision: formState.employer_decision,
      fraud: formState.fraud,
      hours_worked_per_week,
      previous_leaves,
      has_amendments:
        !isEqual(allEmployerBenefits, formState.employerBenefits) ||
        !isEqual(allPreviousLeaves, formState.previousLeaves) ||
        !isEqual(concurrent_leave, formState.concurrentLeave) ||
        !isEqual(claim.hours_worked_per_week, hours_worked_per_week),
      leave_reason: leaveReason,
      relationship_inaccurate_reason: undefined,
      uses_second_eform_version: !!claim.uses_second_eform_version,
    };

    if (isCaringLeave) {
      const parsedRelationshipComment =
        formState.believeRelationshipAccurate === "No"
          ? formState.relationshipInaccurateReason
          : "";

      payload.believe_relationship_accurate =
        formState.believeRelationshipAccurate;

      payload.relationship_inaccurate_reason = parsedRelationshipComment;
    }

    await props.appLogic.employers.submitClaimReview(absenceId, payload);
  });

  /**
   * Disable default browser behavior resulting in a form submission when a user presses Enter in a text field.
   * On other pages, this behavior is desirable and more accessible, however the behavior is not desired for this page,
   * since there's no way to go back to fix something if someone accidentally submits this page.
   */
  const handleKeyDown = (e) => {
    if (
      e.keyCode === 13 &&
      ["text", "radio", "checkbox"].includes(e.target.type)
    ) {
      e.preventDefault();
    }
  };

  return (
    <div className="maxw-desktop-lg">
      <BackButton />
      <Title>
        {t("pages.employersClaimsReview.title", {
          name: claim.fullName,
        })}
      </Title>
      <Alert state="warning" noIcon>
        <Trans
          i18nKey="pages.employersClaimsReview.instructionsFollowUpDate"
          values={{ date: formatDateRange(claim.follow_up_date) }}
        />
      </Alert>
      <p>{t("pages.employersClaimsReview.instructionsAmendment")}</p>
      {!!claim.employer_dba && (
        <ReviewRow
          level="2"
          label={t("pages.employersClaimsReview.organizationNameLabel")}
          noBorder
          data-test="org-name-row"
        >
          {claim.employer_dba}
        </ReviewRow>
      )}
      <ReviewRow
        level="2"
        label={t("pages.employersClaimsReview.employerIdentifierLabel")}
        noBorder
        data-test="ein-row"
      >
        {claim.employer_fein}
      </ReviewRow>
      <EmployeeInformation claim={claim} />
      <LeaveDetails
        appErrors={appErrors}
        claim={claim}
        documents={certificationDocuments}
        downloadDocument={downloadDocument}
        believeRelationshipAccurate={formState.believeRelationshipAccurate}
        onChangeBelieveRelationshipAccurate={
          handleBelieveRelationshipAccurateChange
        }
        relationshipInaccurateReason={formState.relationshipInaccurateReason}
        onChangeRelationshipInaccurateReason={
          handleRelationshipInaccurateReason
        }
      />
      <LeaveSchedule
        claim={claim}
        hasDocuments={!!certificationDocuments.length}
      />
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <form
        id="employer-review-form"
        onSubmit={handleSubmit}
        method="post"
        onKeyDown={handleKeyDown}
      >
        <SupportingWorkDetails
          appErrors={appErrors}
          clearField={clearField}
          getField={getField}
          getFunctionalInputProps={getFunctionalInputProps}
          initialHoursWorkedPerWeek={claim.hours_worked_per_week}
          updateFields={updateFields}
        />

        <ReviewHeading level="2">
          {t("pages.employersClaimsReview.otherLeavesTitle")}
        </ReviewHeading>
        {!shouldShowV2 && (
          <Trans i18nKey="pages.employersClaimsReview.otherLeavesBodyV1" />
        )}
        {shouldShowV2 && (
          <React.Fragment>
            <Trans
              i18nKey="pages.employersClaimsReview.otherLeavesBody"
              components={{
                ul: <ul className="usa-list" />,
                li: <li />,
              }}
            />
            <div className="usa-summary-box" role="complementary">
              <div className="usa-summary-box__body">
                <Heading
                  className="usa-summary-box__heading"
                  level="3"
                  size="4"
                >
                  {t("pages.employersClaimsReview.otherLeavesSummaryBoxTitle")}
                </Heading>
                <div className="usa-summary-box__text">
                  <Trans
                    i18nKey="pages.employersClaimsReview.otherLeavesSummaryBoxBody"
                    components={{
                      ul: <ul className="usa-list" />,
                      li: <li />,
                    }}
                  />
                </div>
              </div>
            </div>
            <PreviousLeaves
              appErrors={appErrors}
              previousLeaves={formState.previousLeaves}
              addedPreviousLeaves={formState.addedPreviousLeaves}
              onAdd={handlePreviousLeaveAdd}
              onChange={handlePreviousLeavesChange}
              onRemove={handlePreviousLeaveRemove}
              shouldShowV2={shouldShowV2}
            />
            <ConcurrentLeave
              appErrors={appErrors}
              addedConcurrentLeave={formState.addedConcurrentLeave}
              concurrentLeave={formState.concurrentLeave}
              onAdd={handleConcurrentLeaveAdd}
              onChange={handleConcurrentLeaveInputChange}
              onRemove={handleConcurrentLeaveRemove}
            />
          </React.Fragment>
        )}
        <EmployerBenefits
          appErrors={appErrors}
          employerBenefits={formState.employerBenefits}
          addedBenefits={formState.addedBenefits}
          onAdd={handleBenefitInputAdd}
          onChange={handleBenefitInputChange}
          onRemove={handleBenefitRemove}
          shouldShowV2={shouldShowV2}
        />
        <FraudReport
          fraudInput={formState.fraud}
          getFunctionalInputProps={getFunctionalInputProps}
        />
        <EmployeeNotice
          employeeNoticeInput={formState.employee_notice}
          fraudInput={formState.fraud}
          getFunctionalInputProps={getFunctionalInputProps}
          updateFields={updateFields}
        />
        <EmployerDecision
          employerDecisionInput={formState.employer_decision}
          fraud={formState.fraud}
          getFunctionalInputProps={getFunctionalInputProps}
          updateFields={updateFields}
        />
        <Feedback
          context={buildFeedbackContext()}
          getFunctionalInputProps={getFunctionalInputProps}
          shouldDisableNoOption={
            isDenyingRequest || isEmployeeNoticeInsufficient
          }
          shouldShowCommentBox={shouldShowCommentBox}
        />
        <Button
          className="margin-top-4"
          type="submit"
          loading={handleSubmit.isThrottled}
          loadingMessage={t("pages.employersClaimsReview.submitLoadingMessage")}
          disabled={isSubmitDisabled}
        >
          {t("pages.employersClaimsReview.submitButton")}
        </Button>
      </form>
    </div>
  );
};

export default withEmployerClaim(Review);
