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

export const fields = ["claim.has_previous_leaves_other_reason"];

export const PreviousLeavesOtherReason = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
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

  const hintList = t("pages.claimsPreviousLeavesOtherReason.hintList", {
    returnObjects: true,
  });

  const handleSave = async () => {
    const patchData = { ...formState };
    if (
      patchData.has_previous_leaves_other_reason === false &&
      get(claim, "previous_leaves_other_reason.length")
    ) {
      patchData.previous_leaves_other_reason = null;
    }
    await appLogic.benefitsApplications.update(claim.application_id, patchData);
  };

  return (
    <QuestionPage
      title={t("pages.claimsPreviousLeavesOtherReason.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_previous_leaves_other_reason")}
        type="radio"
        choices={[
          {
            checked: formState.has_previous_leaves_other_reason === true,
            label: t("pages.claimsPreviousLeavesOtherReason.choiceYes"),
            value: "true",
          },
          {
            checked: formState.has_previous_leaves_other_reason === false,
            label: t("pages.claimsPreviousLeavesOtherReason.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsPreviousLeavesOtherReason.sectionLabel", {
          leaveStartDate,
        })}
        hint={
          <React.Fragment>
            <p>{t("pages.claimsPreviousLeavesOtherReason.hintHeader")}</p>
            <ul className="usa-list">
              {hintList.map((listItem, index) => (
                <li key={index}>{listItem}</li>
              ))}
            </ul>
          </React.Fragment>
        }
      />
    </QuestionPage>
  );
};

PreviousLeavesOtherReason.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(PreviousLeavesOtherReason);
