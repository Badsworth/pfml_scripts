import EmployerBenefit, {
  EmployerBenefitType,
} from "../../../models/EmployerBenefit";
import EmployerClaim, {
  FineosEmployerBenefitType,
} from "../../../models/EmployerClaim";
import React, { useEffect, useState } from "react";
import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/Button";
import EmployeeInformation from "../../../components/employers/EmployeeInformation";
import EmployeeNotice from "../../../components/employers/EmployeeNotice";
import EmployerBenefits from "../../../components/employers/EmployerBenefits";
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
import findKeyByValue from "../../../utils/findKeyByValue";
import formatDateRange from "../../../utils/formatDateRange";
import { pick } from "lodash";
import updateAmendments from "../../../utils/updateAmendments";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

// TODO (EMPLOYER-519): Remove `hoursWorkedPerWeek` when BE provides value
const hoursWorkedPerWeek = 0;

export const Review = (props) => {
  // TODO (EMPLOYER-583) add frontend validation
  const {
    appLogic,
    query: { absence_id: absenceId },
  } = props;
  const {
    employers: { claim },
  } = appLogic;
  const { t } = useTranslation();
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
      (benefit, index) => new EmployerBenefit({ id: index, ...benefit })
    );
    const indexedPreviousLeaves = claim.previous_leaves.map(
      (leave, index) => new PreviousLeave({ id: index, ...leave })
    );
    if (claim) {
      updateFields({
        amendedBenefits: indexedEmployerBenefits,
        employerBenefits: indexedEmployerBenefits,
        amendedLeaves: indexedPreviousLeaves,
        previousLeaves: indexedPreviousLeaves,
        amendedHours: claim.hours_worked_per_week || hoursWorkedPerWeek,
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

    const employer_benefits = formState.amendedBenefits.map((benefit) => {
      const benefitKey = findKeyByValue(
        FineosEmployerBenefitType,
        benefit.benefit_type
      );
      return {
        ...benefit,
        benefit_type: EmployerBenefitType[benefitKey],
      };
    });
    const previous_leaves = formState.amendedLeaves.map((leave) =>
      pick(leave, ["leave_end_date", "leave_start_date"])
    );

    const payload = {
      comment: formState.comment,
      employer_benefits,
      employer_decision: formState.employerDecision,
      fraud: formState.fraud,
      hours_worked_per_week: parseInt(formState.amendedHours),
      previous_leaves,
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
      <p>{t("pages.employersClaimsReview.instructionsComment")}</p>
      <p className="text-bold" aria-labelledby="employerIdentifierNumber">
        {t("pages.employersClaimsReview.employerIdentifierLabel")}
      </p>
      <p className="margin-top-0">{claim.employer_fein}</p>
      <EmployeeInformation claim={claim} />
      <LeaveDetails claim={claim} />
      <LeaveSchedule appLogic={appLogic} claim={claim} />
      <form id="employer-review-form" onSubmit={handleSubmit}>
        <SupportingWorkDetails
          // TODO (EMPLOYER-519): Change `hoursWorkedPerWeek` to `claim.hours_worked_per_week` when BE provides value
          hoursWorkedPerWeek={claim.hours_worked_per_week || hoursWorkedPerWeek}
          onChange={handleHoursWorkedChange}
        />
        <EmployerBenefits
          employerBenefits={formState.employerBenefits}
          onChange={handleBenefitInputChange}
        />
        <PreviousLeaves
          previousLeaves={formState.previousLeaves}
          onChange={handlePreviousLeavesChange}
        />
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
  }).isRequired,
  query: PropTypes.shape({
    absence_id: PropTypes.string.isRequired,
  }).isRequired,
};

export default withEmployerClaim(Review);
