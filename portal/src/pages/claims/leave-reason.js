import Claim from "../../models/Claim";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveReasonEnums from "../../models/LeaveReason";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import get from "lodash/get";
import { pick } from "lodash";
import routeWithParams from "../../utils/routeWithParams";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

export const fields = ["leave_details.reason"];

export const LeaveReason = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props.claim, fields));
  const reason = get(formState, "leave_details.reason");

  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = (formState) =>
    props.appLogic.updateClaim(props.claim.application_id, formState);

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsLeaveReason.title")}
      onSave={handleSave}
      nextPage={routeWithParams("claims.leaveDates", props.query)}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: reason === LeaveReasonEnums.medical,
            hint: t("pages.claimsLeaveReason.medicalLeaveHint"),
            label: t("pages.claimsLeaveReason.medicalLeaveLabel"),
            value: LeaveReasonEnums.medical,
          },
          {
            checked: reason === LeaveReasonEnums.parental,
            hint: t("pages.claimsLeaveReason.parentalLeaveHint"),
            label: t("pages.claimsLeaveReason.parentalLeaveLabel"),
            value: LeaveReasonEnums.parental,
          },
          {
            // TODO: We need to more accurately map this Family Leave option to signify that
            // this is active duty family leave, as opposed to another family leave type.
            // https://lwd.atlassian.net/browse/CP-515
            checked: reason === LeaveReasonEnums.family,
            hint: t("pages.claimsLeaveReason.activeDutyFamilyLeaveHint"),
            label: t("pages.claimsLeaveReason.activeDutyFamilyLeaveLabel"),
            value: LeaveReasonEnums.family,
          },
        ]}
        label={t("pages.claimsLeaveReason.sectionLabel")}
        name="leave_details.reason"
        onChange={handleInputChange}
        type="radio"
      />
    </QuestionPage>
  );
};

LeaveReason.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(LeaveReason);
