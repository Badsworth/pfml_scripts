import BenefitsApplication from "../../models/BenefitsApplication";
import Heading from "../../components/Heading";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { get } from "lodash";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [];

export const PreviousLeavesOtherReasonDetails = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, query } = props;
  const leaveStartDate =
    get(claim, "leave_details.continuous_leave_periods[0].start_date") ||
    get(claim, "leave_details.intermittent_leave_periods[0].start_date");

  const handleSave = () => {
    appLogic.portalFlow.goToNextPage({ claim }, query);
  };

  // TODO (CP-2097) Update page content; use the old previous leaves page for implementation reference.
  // See https://github.com/EOLWD/pfml/blob/730154cc4ef4dba1c33e97ac96e87c8731715b46/portal/src/pages/applications/previous-leaves-details.js
  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeavesOtherReasonDetails.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsPreviousLeavesOtherReasonDetails.sectionLabel", {
          leaveStartDate,
        })}
      </Heading>
    </QuestionPage>
  );
};

PreviousLeavesOtherReasonDetails.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withBenefitsApplication(PreviousLeavesOtherReasonDetails);
