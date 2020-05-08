import Claim from "../../models/Claim";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import claimsApi from "../../api/claimsApi";
import routeWithParams from "../../utils/routeWithParams";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import useHandleSave from "../../hooks/useHandleSave";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

export const LeaveType = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(props.claim);

  const handleInputChange = useHandleInputChange(updateFields);
  const { leave_type } = formState;

  const handleSave = useHandleSave(
    (formState) => claimsApi.updateClaim(new Claim(formState)),
    (result) => props.updateClaim(result.claim)
  );

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsLeaveType.title")}
      onSave={handleSave}
      nextPage={routeWithParams("claims.leaveDates", props.query)}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: leave_type === "medicalLeave",
            hint: t("pages.claimsLeaveType.medicalLeaveHint"),
            label: t("pages.claimsLeaveType.medicalLeaveLabel"),
            value: "medicalLeave",
          },
          {
            checked: leave_type === "parentalLeave",
            hint: t("pages.claimsLeaveType.parentalLeaveHint"),
            label: t("pages.claimsLeaveType.parentalLeaveLabel"),
            value: "parentalLeave",
          },
          {
            checked: leave_type === "activeDutyFamilyLeave",
            hint: t("pages.claimsLeaveType.activeDutyFamilyLeaveHint"),
            label: t("pages.claimsLeaveType.activeDutyFamilyLeaveLabel"),
            value: "activeDutyFamilyLeave",
          },
        ]}
        label={t("pages.claimsLeaveType.sectionLabel")}
        name="leave_type"
        onChange={handleInputChange}
        type="radio"
      />
    </QuestionPage>
  );
};

LeaveType.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  updateClaim: PropTypes.func,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(LeaveType);
