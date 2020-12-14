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
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

export const Review = (props) => {
  // TODO (EMPLOYER-583) add frontend validation
  const {
    appLogic,
    query: { absence_id: absenceId },
  } = props;
  const {
    employers: { claim },
  } = appLogic;

  // explicitly check for false as opposed to falsy values.
  // temporarily allows the redirect behavior to work even
  // if the API has not been updated to populate the field.
  if (claim.is_reviewable === false) {
    appLogic.portalFlow.goTo(routes.employers.status, {
      absence_id: absenceId,
    });
  }

  const { t } = useTranslation();
  const shouldShowPreviousLeaves = isFeatureEnabled(
    "employerShowPreviousLeaves"
  );
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
    const indexedEmployerBenefits = claim.employer_benefits.map(
      (benefit, index) =>
        new EmployerBenefit({ employer_benefit_id: index, ...benefit })
    );
    const indexedPreviousLeaves = claim.previous_leaves.map(
      (leave, index) =>
        new PreviousLeave({ previous_leave_id: index, ...leave })
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

  const handleSubmit = async (event) => {
    event.preventDefault();

    const amendedHours = parseInt(formState.amendedHours);
    const previous_leaves = formState.amendedLeaves.map((leave) =>
      pick(leave, ["leave_end_date", "leave_start_date"])
    );

    const payload = {
      comment: formState.comment,
      employer_benefits: formState.employerBenefits,
      employer_decision: formState.employerDecision,
      fraud: formState.fraud,
      hours_worked_per_week: amendedHours,
      previous_leaves,
      has_amendments:
        !isEqual(formState.amendedBenefits, formState.employerBenefits) ||
        !isEqual(formState.amendedLeaves, formState.previousLeaves) ||
        !isEqual(amendedHours, claim.hours_worked_per_week),
    };
    await props.appLogic.employers.submit(absenceId, payload);
  };

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
      <p className="text-bold" aria-labelledby="employerIdentifierNumber">
        {t("pages.employersClaimsReview.employerIdentifierLabel")}
      </p>
      <p className="margin-top-0">{claim.employer_fein}</p>
      <EmployeeInformation claim={claim} />
      <LeaveDetails claim={claim} />
      <LeaveSchedule appLogic={appLogic} claim={claim} />
      <form id="employer-review-form" onSubmit={handleSubmit}>
        <SupportingWorkDetails
          hoursWorkedPerWeek={claim.hours_worked_per_week}
          onChange={handleHoursWorkedChange}
        />
        <EmployerBenefits
          employerBenefits={formState.employerBenefits}
          onChange={handleBenefitInputChange}
        />
        {/* TODO (EMPLOYER-656): Show previous leaves */}
        {shouldShowPreviousLeaves && (
          <PreviousLeaves
            previousLeaves={formState.previousLeaves}
            onChange={handlePreviousLeavesChange}
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
      submit: PropTypes.func.isRequired,
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
