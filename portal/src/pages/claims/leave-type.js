import InputChoiceGroup from "../../components/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "react-i18next";

const LeaveType = (props) => {
  const { t } = useTranslation();

  // TODO get current claim id from query parameter, then get current claim
  // TODO initialState for form should come from current claim
  // const { claimId } = props.query;
  // const claim = props.claims.byId[claimId];
  // const { formState, updateFields, removeField } = useFormState(claim);
  // For now just initialize to empty formState
  const { formState, updateFields } = useFormState();
  const handleInputChange = useHandleInputChange(updateFields);
  const { leaveType } = formState;

  // TODO call API once API module is ready
  // const handleSave = useHandleSave(api.patchClaim, props.setClaim);
  // TODO save the API result to the claim once we have a `setClaim` function we can use
  // For now just do nothing.
  const handleSave = async () => {};

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsLeaveType.title")}
      onSave={handleSave}
      // TO-DO: Update route when the next page is created
      nextPage={routes.home}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: leaveType === "medicalLeave",
            hint: t("pages.claimsLeaveType.medicalLeaveHint"),
            label: t("pages.claimsLeaveType.medicalLeaveLabel"),
            value: "medicalLeave",
          },
          {
            checked: leaveType === "parentalLeave",
            hint: t("pages.claimsLeaveType.parentalLeaveHint"),
            label: t("pages.claimsLeaveType.parentalLeaveLabel"),
            value: "parentalLeave",
          },
          {
            checked: leaveType === "activeDutyFamilyLeave",
            hint: t("pages.claimsLeaveType.activeDutyFamilyLeaveHint"),
            label: t("pages.claimsLeaveType.activeDutyFamilyLeaveLabel"),
            value: "activeDutyFamilyLeave",
          },
        ]}
        label={t("pages.claimsLeaveType.sectionLabel")}
        name="leaveType"
        onChange={handleInputChange}
        type="radio"
      />
    </QuestionPage>
  );
};

export default LeaveType;
