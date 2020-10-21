import React, { useState } from "react";
import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import EmployeeInformation from "../../../components/employers/EmployeeInformation";
import EmployerBenefits from "../../../components/employers/EmployerBenefits";
import Feedback from "../../../components/employers/Feedback";
import LeaveDetails from "../../../components/employers/LeaveDetails";
import LeaveSchedule from "../../../components/employers/LeaveSchedule";
import PreviousLeaves from "../../../components/employers/PreviousLeaves";
import PropTypes from "prop-types";
import SupportingWorkDetails from "../../../components/employers/SupportingWorkDetails";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import { claim } from "../../../../tests/test-utils";
import formatDateRange from "../../../utils/formatDateRange";
import updateAmendments from "../../../utils/updateAmendments";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

// TODO (EMPLOYER-364): Remove hardcoded date and mock claim data
const employerDueDate = formatDateRange("2020-10-10");

export const Review = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();
  const {
    fineos_absence_id,
    employer_fein,
    hours_worked_per_week,
    employer_benefits,
    previous_leaves,
  } = claim;
  const [amendedBenefits, setAmendedBenefits] = useState(employer_benefits);
  const [amendedLeaves, setAmendedLeaves] = useState(previous_leaves);
  const [amendedHours, setAmendedHours] = useState(hours_worked_per_week);

  const handleBenefitInputChange = (updatedBenefit) => {
    const updatedBenefits = updateAmendments(amendedBenefits, updatedBenefit);
    setAmendedBenefits(updatedBenefits);
  };

  const handlePreviousLeavesChange = (updatedLeave) => {
    const updatedPreviousLeaves = updateAmendments(amendedLeaves, updatedLeave);
    setAmendedLeaves(updatedPreviousLeaves);
  };

  const handleSubmit = async ({ comment }) => {
    await appLogic.employers.submit(fineos_absence_id, {
      employer_benefits: amendedBenefits,
      previous_leaves: amendedLeaves,
      hours_worked_per_week: parseInt(amendedHours),
      comment,
    });
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
          values={{ date: employerDueDate }}
        />
      </Alert>
      <p aria-labelledby="instructionsAmendment">
        {t("pages.employersClaimsReview.instructionsAmendment")}
      </p>
      <p aria-labelledby="instructionsComment">
        {t("pages.employersClaimsReview.instructionsComment")}
      </p>
      <p className="text-bold" aria-labelledby="employerIdentifierNumber">
        {t("pages.employersClaimsReview.employerIdentifierLabel")}
      </p>
      <p className="margin-top-0">{employer_fein}</p>
      <EmployeeInformation claim={claim} />
      <LeaveDetails claim={claim} />
      <LeaveSchedule claim={claim} />
      <SupportingWorkDetails
        hoursWorkedPerWeek={hours_worked_per_week}
        onChange={setAmendedHours}
      />
      <EmployerBenefits
        benefits={employer_benefits}
        onChange={handleBenefitInputChange}
      />
      <PreviousLeaves
        previousLeaves={previous_leaves}
        onChange={handlePreviousLeavesChange}
      />
      <Feedback appLogic={props.appLogic} onSubmit={handleSubmit} />
    </React.Fragment>
  );
};

Review.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default withUser(Review);
