import BenefitsApplication from "../../models/BenefitsApplication";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.tax_identifier"];

/**
 * A form page to capture the worker's SSN or ITIN.
 */
export const Ssn = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage title={t("pages.claimsSsn.title")} onSave={handleSave}>
      <InputText
        {...getFunctionalInputProps("tax_identifier")}
        mask="ssn"
        pii
        label={t("pages.claimsSsn.sectionLabel")}
        hint={t("pages.claimsSsn.lead")}
      />
    </QuestionPage>
  );
};

Ssn.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  appLogic: PropTypes.object.isRequired,
};

export default withBenefitsApplication(Ssn);
