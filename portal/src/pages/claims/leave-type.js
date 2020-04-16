import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { connect } from "react-redux";
import routes from "../../routes";
import { updateFieldFromEvent } from "../../actions";
import { useTranslation } from "react-i18next";

export const LeaveType = (props) => {
  const { t } = useTranslation();
  const { leaveType } = props.formData;

  return (
    <QuestionPage
      title={t("pages.claimsLeaveType.title")}
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
        onChange={props.updateFieldFromEvent}
        type="radio"
      />
    </QuestionPage>
  );
};

LeaveType.propTypes = {
  formData: PropTypes.shape({
    leaveType: PropTypes.oneOf([
      "activeDutyFamilyLeave",
      "medicalLeave",
      "parentalLeave",
    ]),
  }).isRequired,
  updateFieldFromEvent: PropTypes.func.isRequired,
};

const mapStateToProps = (state) => ({
  formData: state.form,
});

const mapDispatchToProps = { updateFieldFromEvent };

export default connect(mapStateToProps, mapDispatchToProps)(LeaveType);
