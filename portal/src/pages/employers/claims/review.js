import React, { useEffect, useState } from "react";
import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import Claim from "../../../models/Claim";
import EmployeeInformation from "../../../components/employers/EmployeeInformation";
import EmployerBenefit from "../../../models/EmployerBenefit";
import EmployerBenefits from "../../../components/employers/EmployerBenefits";
import EmployerDecision from "../../../components/employers/EmployerDecision";
import Feedback from "../../../components/employers/Feedback";
import FraudReport from "../../../components/employers/FraudReport";
import LeaveDetails from "../../../components/employers/LeaveDetails";
import LeaveSchedule from "../../../components/employers/LeaveSchedule";
import PreviousLeave from "../../../models/PreviousLeave";
import PreviousLeaves from "../../../components/employers/PreviousLeaves";
import PropTypes from "prop-types";
import Spinner from "../../../components/Spinner";
import SupportingWorkDetails from "../../../components/employers/SupportingWorkDetails";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import formatDateRange from "../../../utils/formatDateRange";
import updateAmendments from "../../../utils/updateAmendments";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

// TODO (EMPLOYER-363): Update respond by date
const employerDueDate = "2020-10-10";
// TODO (EMPLOYER-519): Remove `hoursWorkedPerWeek` when BE provides value
const hoursWorkedPerWeek = 40;

export const Review = (props) => {
  const {
    appLogic,
    retrievedClaim,
    query: { absence_id: absenceId },
  } = props;
  const { t } = useTranslation();
  const claim = retrievedClaim || appLogic.employers.claim;
  const [amendedBenefits, setAmendedBenefits] = useState([]);
  const [amendedLeaves, setAmendedLeaves] = useState([]);
  const [amendedHours, setAmendedHours] = useState(0);
  const [fraud, setFraud] = useState();
  const [employerDecision, setEmployerDecision] = useState();

  // TODO (EMPLOYER-500): Remove logic in favor of `withEmployerClaim` HOC
  useEffect(() => {
    if (!claim) {
      appLogic.employers.load(absenceId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claim, absenceId]);

  useEffect(() => {
    if (claim) {
      setAmendedBenefits(claim.employer_benefits);
      setAmendedLeaves(claim.previous_leaves);
      // TODO (EMPLOYER-519): Remove `hoursWorkedPerWeek` value when BE provides value
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
    await appLogic.employers.submit(absenceId, {
      employer_benefits: amendedBenefits,
      previous_leaves: amendedLeaves,
      hours_worked_per_week: parseInt(amendedHours),
      comment,
      employer_decision: employerDecision,
      fraud,
    });
  };

  return (
    <React.Fragment>
      {/* TODO (EMPLOYER-500): Remove logic in favor of `withEmployerClaim` HOC */}
      {!claim && (
        <div className="margin-top-8 text-center">
          <Spinner aria-valuetext={t("components.spinner.label")} />
        </div>
      )}
      {claim && (
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
            hoursWorkedPerWeek={hoursWorkedPerWeek}
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
          <EmployerDecision
            onChange={handleEmployerDecisionChange}
            fraud={fraud}
          />
          <Feedback
            appLogic={props.appLogic}
            fraud={fraud}
            onSubmit={handleSubmit}
          />
        </React.Fragment>
      )}
    </React.Fragment>
  );
};

Review.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    employers: PropTypes.shape({
      load: PropTypes.func.isRequired,
      submit: PropTypes.func.isRequired,
      claim: PropTypes.shape({
        employer_benefits: PropTypes.arrayOf(
          PropTypes.instanceOf(EmployerBenefit)
        ),
        employer_fein: PropTypes.string,
        fullName: PropTypes.string,
        hours_worked_per_week: PropTypes.number,
        previous_leaves: PropTypes.arrayOf(PropTypes.instanceOf(PreviousLeave)),
      }),
    }).isRequired,
  }).isRequired,
  retrievedClaim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    absence_id: PropTypes.string.isRequired,
  }).isRequired,
};

export default withUser(Review);
