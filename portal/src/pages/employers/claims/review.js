import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import EmployeeInformation from "../../../components/employers/EmployeeInformation";
import EmployerBenefits from "../../../components/employers/EmployerBenefits";
import Feedback from "../../../components/employers/Feedback";
import LeaveDetails from "../../../components/employers/LeaveDetails";
import LeaveSchedule from "../../../components/employers/LeaveSchedule";
import PreviousLeaves from "../../../components/employers/PreviousLeaves";
import PropTypes from "prop-types";
import React from "react";
import SupportingWorkDetails from "../../../components/employers/SupportingWorkDetails";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import { claim } from "../../../../tests/test-utils";
import formatDateRange from "../../../utils/formatDateRange";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

const employerDueDate = formatDateRange("2020-09-28");

const Review = (props) => {
  const { t } = useTranslation();
  const {
    fineos_absence_id,
    first_name,
    employer_fein,
    last_name,
    leave_details: { intermittent_leave_periods },
    middle_name,
    employer_benefits,
    previous_leaves,
  } = claim;
  const name = `${first_name} ${middle_name} ${last_name}`
    .split(/\s+/)
    .join(" ");

  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.employersClaimsReview.title", { name })}</Title>
      <Alert state="warning" noIcon>
        <Trans
          i18nKey="pages.employersClaimsReview.instructionsDueDate"
          components={{
            emphasized: <strong />,
          }}
          values={{ date: employerDueDate }}
        />
      </Alert>
      <p aria-labelledby="instructionsAmendment">
        {t("pages.employersClaimsReview.instructionsAmendment")}
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
      <EmployerBenefits benefits={employer_benefits} />
      <PreviousLeaves previousLeaves={previous_leaves} />
      <Feedback appLogic={props.appLogic} claimId={fineos_absence_id} />
    </React.Fragment>
  );
};

Review.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default withUser(Review);
