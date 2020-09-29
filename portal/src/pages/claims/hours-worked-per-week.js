import Claim from "../../models/Claim";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.hours_worked_per_week"];

export const HoursWorkedPerWeek = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsHoursWorkedPerWeek.title")}
      onSave={handleSave}
    >
      <InputText
        {...getFunctionalInputProps("hours_worked_per_week")}
        label={t("pages.claimsHoursWorkedPerWeek.sectionLabel")}
        hint={t("pages.claimsHoursWorkedPerWeek.hint")}
        width="small"
      />
    </QuestionPage>
  );
};

HoursWorkedPerWeek.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(HoursWorkedPerWeek);
