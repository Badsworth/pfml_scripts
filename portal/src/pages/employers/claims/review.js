import BackButton from "../../../components/BackButton";
import EmployeeInformation from "../../../components/employers/EmployeeInformation";
import EmployerBenefits from "../../../components/employers/EmployerBenefits";
import Feedback from "../../../components/employers/Feedback";
import LeaveDetails from "../../../components/employers/LeaveDetails";
import LeaveSchedule from "../../../components/employers/LeaveSchedule";
import PastLeave from "../../../components/employers/PastLeave";
import PropTypes from "prop-types";
import React from "react";
import SupportingWorkDetails from "../../../components/employers/SupportingWorkDetails";
import Title from "../../../components/Title";
import { claim } from "../../../../tests/test-utils";
import formatDateRange from "../../../utils/formatDateRange";
import { useTranslation } from "../../../locales/i18n";

const employerDueDate = formatDateRange("2020-09-28");

const Review = (props) => {
  const { t } = useTranslation();
  const {
    employer_fein,
    leave_details: { intermittent_leave_periods },
    employer_benefits,
    previous_leaves,
  } = claim;

  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.employersClaimsReview.title")}</Title>
      <p aria-labelledby="instructionsAmendment">
        {t("pages.employersClaimsReview.instructionsAmendment")}
      </p>
      <p aria-labelledby="instructionsDueDate">
        {t("pages.employersClaimsReview.instructionsDueDate", {
          date: employerDueDate,
        })}
      </p>
      <p className="text-bold" aria-labelledby="employerIdentifierNumber">
        {t("pages.employersClaimsReview.employerIdentifierLabel")}
      </p>
      <p className="margin-top-0">{employer_fein}</p>
      <EmployeeInformation claim={claim} />
      <LeaveDetails claim={claim} />
      <LeaveSchedule claim={claim} />
      {claim.isIntermittent && (
        <SupportingWorkDetails
          intermittentLeavePeriods={intermittent_leave_periods}
        />
      )}
      <EmployerBenefits employerBenefits={employer_benefits} />
      <PastLeave previousLeaves={previous_leaves} />
      <Feedback appLogic={props.appLogic} />
    </React.Fragment>
  );
};

Review.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default Review;
