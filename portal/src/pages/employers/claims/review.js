import React, { useEffect, useState } from "react";
import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import EmployeeInformation from "../../../components/employers/EmployeeInformation";
import EmployerBenefits from "../../../components/employers/EmployerBenefits";
import EmployerClaim from "../../../models/EmployerClaim";
import EmployerDecision from "../../../components/employers/EmployerDecision";
import Feedback from "../../../components/employers/Feedback";
import FraudReport from "../../../components/employers/FraudReport";
import LeaveDetails from "../../../components/employers/LeaveDetails";
import LeaveSchedule from "../../../components/employers/LeaveSchedule";
import PreviousLeaves from "../../../components/employers/PreviousLeaves";
import PropTypes from "prop-types";
import SupportingWorkDetails from "../../../components/employers/SupportingWorkDetails";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import formatDateRange from "../../../utils/formatDateRange";
import updateAmendments from "../../../utils/updateAmendments";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

// TODO (EMPLOYER-363): Update respond by date
const employerDueDate = "2020-10-10";
// TODO (EMPLOYER-519): Remove `hoursWorkedPerWeek` when BE provides value
const hoursWorkedPerWeek = 40;

export const Review = (props) => {
  // TODO (EMPLOYER-583) add frontend validation
  const {
    appLogic: {
      employers: { claim },
    },
    query: { absence_id: absenceId },
  } = props;
  const { t } = useTranslation();
  const [amendedBenefits, setAmendedBenefits] = useState([]);
  const [amendedLeaves, setAmendedLeaves] = useState([]);
  const [amendedHours, setAmendedHours] = useState(0);
  const [fraud, setFraud] = useState();
  const [employerDecision, setEmployerDecision] = useState();

  useEffect(() => {
    if (claim) {
      setAmendedBenefits(claim.employer_benefits);
      setAmendedLeaves(claim.previous_leaves);
      setAmendedHours(claim.hours_worked_per_week || hoursWorkedPerWeek);
    }
  }, [claim]);

  const handleBenefitInputChange = (updatedBenefit) => {
    const updatedBenefits = updateAmendments(amendedBenefits, updatedBenefit);
    setAmendedBenefits(updatedBenefits);
  };

  const handlePreviousLeavesChange = (updatedLeave) => {
    const updatedPreviousLeaves = updateAmendments(amendedLeaves, updatedLeave);
    setAmendedLeaves(updatedPreviousLeaves);
  };

  const handleFraudInputChange = (updatedFraudInput) => {
    setFraud(updatedFraudInput);
  };

  const handleEmployerDecisionChange = (updatedEmployerDecision) => {
    setEmployerDecision(updatedEmployerDecision);
  };

  const handleSubmit = async ({ comment }) => {
    const payload = {
      comment,
      employer_benefits: amendedBenefits,
      employer_decision: employerDecision,
      fraud,
      hours_worked_per_week: parseInt(amendedHours),
      previous_leaves: amendedLeaves,
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
          i18nKey="pages.employersClaimsReview.instructionsDueDate"
          values={{ date: formatDateRange(employerDueDate) }}
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
      <LeaveSchedule claim={claim} />
      <SupportingWorkDetails
        // TODO (EMPLOYER-519): Change `hoursWorkedPerWeek` to `claim.hours_worked_per_week` when BE provides value
        hoursWorkedPerWeek={claim.hours_worked_per_week || hoursWorkedPerWeek}
        onChange={setAmendedHours}
      />
      <EmployerBenefits
        benefits={claim.employer_benefits}
        onChange={handleBenefitInputChange}
      />
      <PreviousLeaves
        previousLeaves={claim.previous_leaves}
        onChange={handlePreviousLeavesChange}
      />
      <FraudReport onChange={handleFraudInputChange} />
      <EmployerDecision onChange={handleEmployerDecisionChange} fraud={fraud} />
      <Feedback
        appLogic={props.appLogic}
        employerDecision={employerDecision}
        onSubmit={handleSubmit}
      />
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
