import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import Fieldset from "src/components/core/Fieldset";
import FormLabel from "src/components/core/FormLabel";
import InputText from "../../components/core/InputText";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.tax_identifier", "claim.employer_fein"];

/**
 * A form page to recapture the worker's SSN end FEIN.
 */
export const AdditionalUserNotFoundInfoSsnFien = (
  props: WithBenefitsApplicationProps
) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    tax_identifier: "",
    employer_fein: "",
  });

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <Fieldset>
        <FormLabel
          component="legend"
          hint={t(
            "pages.noEmployeeEmployerMatchFlow.noEmployeeEmployerMatchDescription"
          )}
        >
          {t("pages.noEmployeeEmployerMatchFlow.noEmployeeEmployerMatchTitle")}
        </FormLabel>
        <InputText
          {...getFunctionalInputProps("tax_identifier")}
          mask="ssn"
          pii
          label={t(
            "pages.noEmployeeEmployerMatchFlow.noEmployeeEmployerMatchSsnLabel"
          )}
          hint=""
          smallLabel={true}
        />
        <InputText
          {...getFunctionalInputProps("employer_fein")}
          inputMode="numeric"
          label={t(
            "pages.noEmployeeEmployerMatchFlow.noEmployeeEmployerMatchFeinLabel"
          )}
          mask="fein"
          hint=""
          smallLabel={true}
        />
      </Fieldset>
    </QuestionPage>
  );
};

export default withBenefitsApplication(AdditionalUserNotFoundInfoSsnFien);
