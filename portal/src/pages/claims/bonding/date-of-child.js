import InputDate from "../../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";
import withClaim from "../../../hoc/withClaim";

export const fields = ["claim.temp.leave_details.bonding.date_of_child"];

export const DateOfChild = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () => {
    appLogic.claims.update(claim.application_id, formState);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsBondingDateOfChild.title")}
      onSave={handleSave}
    >
      <InputDate
        {...getFunctionalInputProps("temp.leave_details.bonding.date_of_child")}
        label={t("pages.claimsBondingDateOfChild.sectionLabel")}
        example={t("components.form.dateInputExample")}
        hint={t("pages.claimsBondingDateOfChild.hint")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />
    </QuestionPage>
  );
};

DateOfChild.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(DateOfChild);
