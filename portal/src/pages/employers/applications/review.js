import React, { useEffect, useState } from "react";
import { isEqual, pick } from "lodash";
import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/Button";
import EmployeeInformation from "../../../components/employers/EmployeeInformation";
import EmployeeNotice from "../../../components/employers/EmployeeNotice";
import EmployerBenefit from "../../../models/EmployerBenefit";
import EmployerBenefits from "../../../components/employers/EmployerBenefits";
import EmployerClaim from "../../../models/EmployerClaim";
import EmployerDecision from "../../../components/employers/EmployerDecision";
import Feedback from "../../../components/employers/Feedback";
import FraudReport from "../../../components/employers/FraudReport";
import LeaveDetails from "../../../components/employers/LeaveDetails";
import LeaveSchedule from "../../../components/employers/LeaveSchedule";
import PreviousLeave from "../../../models/PreviousLeave";
import PreviousLeaves from "../../../components/employers/PreviousLeaves";
import PropTypes from "prop-types";
import SupportingWorkDetails from "../../../components/employers/SupportingWorkDetails";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import formatDateRange from "../../../utils/formatDateRange";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import updateAmendments from "../../../utils/updateAmendments";
import useThrottledHandler from "../../../hooks/useThrottledHandler";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

export const Review = (props) => {
  // TODO (EMPLOYER-583) add frontend validation
  const {
    appLogic,
    query: { absence_id: absenceId },
  } = props;
  const {
    appErrors,
    employers: { claim },
  } = appLogic;
  const { t } = useTranslation();
  // TODO (EMPLOYER-718): Remove feature flag
  const showPreviousLeaves = isFeatureEnabled("employerShowPreviousLeaves");

  // explicitly check for false as opposed to falsy values.
  // temporarily allows the redirect behavior to work even
  // if the API has not been updated to populate the field.
  if (claim.is_reviewable === false) {
    appLogic.portalFlow.goTo(routes.employers.status, {
      absence_id: absenceId,
    });
  }

  const [formState, setFormState] = useState({
    employerBenefits: [],
    previousLeaves: [],
    amendedBenefits: [],
    amendedLeaves: [],
    amendedHours: 0,
    comment: "",
    employerDecision: undefined,
    fraud: undefined,
    employeeNotice: undefined,
  });
  const isCommentRequired =
    formState.fraud === "Yes" ||
    formState.employerDecision === "Deny" ||
    formState.employeeNotice === "No";

  useEffect(() => {
    // Generate id based on index for employer benefit, previous leave (id is not provided by BE)
    // Note: these indices are used to properly display inline errors and amend employer benefits and
    // previous leaves. If employer_benefit_id and previous_leave_id no longer match the indices, then
    // the functionality described above will need to be reimplemented.
    const indexedEmployerBenefits = claim.employer_benefits.map(
      (benefit, index) =>
        new EmployerBenefit({ ...benefit, employer_benefit_id: index })
    );
    const indexedPreviousLeaves = claim.previous_leaves.map(
      (leave, index) =>
        new PreviousLeave({ ...leave, previous_leave_id: index })
    );
    if (claim) {
      updateFields({
        amendedBenefits: indexedEmployerBenefits,
        employerBenefits: indexedEmployerBenefits,
        amendedLeaves: indexedPreviousLeaves,
        previousLeaves: indexedPreviousLeaves,
        amendedHours: claim.hours_worked_per_week,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claim]);

  const updateFields = (fields) => {
    setFormState({ ...formState, ...fields });
  };

  const handleHoursWorkedChange = (updatedHoursWorked) => {
    updateFields({ amendedHours: updatedHoursWorked });
  };

  const handleBenefitInputChange = (updatedBenefit) => {
    const updatedBenefits = updateAmendments(
      formState.amendedBenefits,
      updatedBenefit
    );
    updateFields({ amendedBenefits: updatedBenefits });
  };

  const handlePreviousLeavesChange = (updatedLeave) => {
    const updatedPreviousLeaves = updateAmendments(
      formState.amendedLeaves,
      updatedLeave
    );
    updateFields({ amendedLeaves: updatedPreviousLeaves });
  };

  const handleFraudInputChange = (updatedFraudInput) => {
    updateFields({ fraud: updatedFraudInput });
  };

  const handleEmployeeNoticeChange = (updatedEmployeeNotice) => {
    updateFields({ employeeNotice: updatedEmployeeNotice });
  };

  const handleEmployerDecisionChange = (updatedEmployerDecision) => {
    updateFields({ employerDecision: updatedEmployerDecision });
  };

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();

    const amendedHours = formState.amendedHours;
    const previous_leaves = formState.amendedLeaves.map((leave) =>
      pick(leave, ["leave_end_date", "leave_reason", "leave_start_date"])
    );
    const employer_benefits = formState.amendedBenefits.map((benefit) =>
      pick(benefit, [
        "benefit_amount_dollars",
        "benefit_amount_frequency",
        "benefit_end_date",
        "benefit_start_date",
        "benefit_type",
      ])
    );
    const payload = {
      comment: formState.comment,
      employer_benefits,
      employer_decision: formState.employerDecision,
      fraud: formState.fraud,
      hours_worked_per_week: amendedHours,
      previous_leaves,
      has_amendments:
        !isEqual(formState.amendedBenefits, formState.employerBenefits) ||
        !isEqual(formState.amendedLeaves, formState.previousLeaves) ||
        !isEqual(amendedHours, claim.hours_worked_per_week),
    };

    await props.appLogic.employers.submitClaimReview(absenceId, payload);
  });

  return (
    <React.Fragment>
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
        <React.Fragment>
          <p className="text-bold">
            {t("pages.employersClaimsReview.organizationNameLabel")}
          </p>
          <p className="margin-top-0">{claim.employer_dba}</p>
        </React.Fragment>
      )}
      <p className="text-bold">
        {t("pages.employersClaimsReview.employerIdentifierLabel")}
      </p>
      <p className="margin-top-0">{claim.employer_fein}</p>
      <EmployeeInformation claim={claim} />
      <LeaveDetails claim={claim} />
      <LeaveSchedule appLogic={appLogic} claim={claim} />
      <form id="employer-review-form" onSubmit={handleSubmit}>
        <SupportingWorkDetails
          appErrors={appErrors}
          hoursWorkedPerWeek={claim.hours_worked_per_week}
          onChange={handleHoursWorkedChange}
        />
        <EmployerBenefits
          appErrors={appErrors}
          employerBenefits={formState.employerBenefits}
          onChange={handleBenefitInputChange}
        />
        {/* TODO (EMPLOYER-718): Remove feature flag  */}
        {showPreviousLeaves && (
          <PreviousLeaves
            appErrors={appErrors}
            onChange={handlePreviousLeavesChange}
            previousLeaves={formState.previousLeaves}
          />
        )}
        <FraudReport onChange={handleFraudInputChange} />
        <EmployeeNotice
          fraud={formState.fraud}
          onChange={handleEmployeeNoticeChange}
        />
        <EmployerDecision
          fraud={formState.fraud}
          onChange={handleEmployerDecisionChange}
        />
        <Feedback
          appLogic={props.appLogic}
          isReportingFraud={formState.fraud === "Yes"}
          isDenyingRequest={formState.employerDecision === "Deny"}
          isEmployeeNoticeInsufficient={formState.employeeNotice === "No"}
          comment={formState.comment}
          setComment={(comment) => updateFields({ comment })}
        />
        <Button
          className="margin-top-4"
          type="submit"
          loading={handleSubmit.isThrottled}
          loadingMessage={t("pages.employersClaimsReview.submitLoadingMessage")}
          disabled={isCommentRequired && formState.comment === ""}
        >
          {t("pages.employersClaimsReview.submitButton")}
        </Button>
      </form>
    </React.Fragment>
  );
};

Review.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    employers: PropTypes.shape({
      claim: PropTypes.instanceOf(EmployerClaim),
      submitClaimReview: PropTypes.func.isRequired,
    }).isRequired,
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }),
  }).isRequired,
  query: PropTypes.shape({
    absence_id: PropTypes.string.isRequired,
  }).isRequired,
};

export default withEmployerClaim(Review);
