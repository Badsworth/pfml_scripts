import Claim, { LeaveReason as LeaveReasonEnum } from "../../models/Claim";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import get from "lodash/get";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.leave_details.reason"];

const LeaveReason = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const reason = get(formState, "leave_details.reason");

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsLeaveReason.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("leave_details.reason")}
        choices={[
          {
            checked: reason === LeaveReasonEnum.medical,
            hint: t("pages.claimsLeaveReason.medicalLeaveHint"),
            label: t("pages.claimsLeaveReason.medicalLeaveLabel"),
            value: LeaveReasonEnum.medical,
          },
          {
            checked: reason === LeaveReasonEnum.bonding,
            hint: t("pages.claimsLeaveReason.bondingLeaveHint"),
            label: t("pages.claimsLeaveReason.bondingLeaveLabel"),
            value: LeaveReasonEnum.bonding,
          },
          {
            // TODO: We need to more accurately map this Family Leave option to signify that
            // this is active duty family leave, as opposed to another family leave type.
            // https://lwd.atlassian.net/browse/CP-515
            checked: reason === LeaveReasonEnum.activeDutyFamily,
            hint: t("pages.claimsLeaveReason.activeDutyFamilyLeaveHint"),
            label: t("pages.claimsLeaveReason.activeDutyFamilyLeaveLabel"),
            value: LeaveReasonEnum.activeDutyFamily,
          },
          {
            // TODO: We need to more accurately map this Family Leave option to signify that
            // this is family leave to care for a service member, as opposed to another family leave type.
            // https://lwd.atlassian.net/browse/CP-515
            checked: reason === LeaveReasonEnum.serviceMemberFamily,
            hint: t("pages.claimsLeaveReason.serviceMemberFamilyLeaveHint"),
            label: t("pages.claimsLeaveReason.serviceMemberFamilyLeaveLabel"),
            value: LeaveReasonEnum.serviceMemberFamily,
          },
        ]}
        label={t("pages.claimsLeaveReason.sectionLabel")}
        type="radio"
      />
    </QuestionPage>
  );
};

LeaveReason.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(LeaveReason);
