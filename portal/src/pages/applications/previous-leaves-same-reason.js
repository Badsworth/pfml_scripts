import { get, pick } from "lodash";
import BenefitsApplication from "../../models/BenefitsApplication";
import { DateTime } from "luxon";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [];

// TODO(CP-2125): Integrate this page with the API. For now we'll use this 'tempFields' array so that
// the Checklist page won't block this step from appearing completed. This is because the Checklist page
// uses the above `fields` array to calculate whether or not a page/Step is completed. With the empty array
// above the page/Step will appear complete regardless of if the API has saved the data to the DB.
export const tempFields = ["claim.has_previous_leaves_same_reason"];

export const PreviousLeavesSameReason = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const { formState, updateFields } = useFormState(
    pick(props, tempFields).claim
  );
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });
  let leaveStartDate =
    get(claim, "leave_details.continuous_leave_periods[0].start_date") ||
    get(claim, "leave_details.intermittent_leave_periods[0].start_date");

  if (leaveStartDate) {
    leaveStartDate = DateTime.fromISO(leaveStartDate).toLocaleString(
      DateTime.DATE_FULL
    );
  }

  const handleSave = () => {
    const patchData = { ...formState };
    if (
      patchData.has_previous_leaves_same_reason === false &&
      get(claim, "previous_leaves_same_reason.length")
    ) {
      patchData.previous_leaves_same_reason = null;
    }
    appLogic.benefitsApplications.update(claim.application_id, patchData);
  };

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeavesSameReason.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_previous_leaves_same_reason")}
        type="radio"
        choices={[
          {
            checked: formState.has_previous_leaves_same_reason === true,
            label: t("pages.claimsPreviousLeavesSameReason.choiceYes"),
            value: "true",
          },
          {
            checked: formState.has_previous_leaves_same_reason === false,
            label: t("pages.claimsPreviousLeavesSameReason.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsPreviousLeavesSameReason.sectionLabel", {
          leaveStartDate,
        })}
      />
    </QuestionPage>
  );
};

PreviousLeavesSameReason.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(PreviousLeavesSameReason);
