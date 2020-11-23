import EmployerBenefit, {
  EmployerBenefitType,
} from "../../../models/EmployerBenefit";
import EmployerClaim, {
  FineosEmployerBenefitType,
} from "../../../models/EmployerClaim";
import React, { useEffect, useState } from "react";
import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import EmployeeInformation from "../../../components/employers/EmployeeInformation";
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
  const [employerBenefits, setEmployerBenefits] = useState([]);
  const [previousLeaves, setPreviousLeaves] = useState([]);
  const [amendedBenefits, setAmendedBenefits] = useState([]);
  const [amendedLeaves, setAmendedLeaves] = useState([]);
  const [amendedHours, setAmendedHours] = useState(0);
  const [fraud, setFraud] = useState();
  const [employerDecision, setEmployerDecision] = useState();

  useEffect(() => {
    if (claim) {
      const indexedEmployerBenefits = claim.employer_benefits.map(
        (benefit, index) => new EmployerBenefit({ id: index, ...benefit })
      );
      const indexedPreviousLeaves = claim.previous_leaves.map(
        (leave, index) => new PreviousLeave({ id: index, ...leave })
      );
      setAmendedBenefits(indexedEmployerBenefits);
      setEmployerBenefits(indexedEmployerBenefits);
      setAmendedLeaves(indexedPreviousLeaves);
      setPreviousLeaves(indexedPreviousLeaves);
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
      employer_benefits: amendedBenefits.map((benefit) => {
        const { benefit_type, ...rest } = benefit;
        const benefitKey = findKeyByValue(
          FineosEmployerBenefitType,
          benefit_type
        );
        return {
          benefit_type: EmployerBenefitType[benefitKey],
          ...rest,
        };
      }),
      employer_decision: employerDecision,
      fraud,
      hours_worked_per_week: parseInt(amendedHours),
      previous_leaves: amendedLeaves.map(
        ({ leave_end_date, leave_start_date }) => {
          return { leave_end_date, leave_start_date };
        }
      ),
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
        employerBenefits={employerBenefits}
        onChange={handleBenefitInputChange}
      />
      <PreviousLeaves
        previousLeaves={previousLeaves}
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
