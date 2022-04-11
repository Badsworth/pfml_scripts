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
export const NoMatchFound = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const includesNoEmployeeFoundError = () => {
    if (
      !(claim.application_id in appLogic.benefitsApplications.warningsLists)
    ) {
      return false;
    }
    return appLogic.benefitsApplications.warningsLists[
      claim.application_id
    ].some((warning) => warning.rule === "require_employee");
  };

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
            "pages.claimsAdditionalUserNotFoundInfo.noMatchFoundDescription"
          )}
        >
          {t(
            "pages.claimsAdditionalUserNotFoundInfo." +
              (includesNoEmployeeFoundError()
                ? "noEmployeeFoundTitle"
                : "noEmployerFoundTitle")
          )}
        </FormLabel>
        <InputText
          {...getFunctionalInputProps("tax_identifier")}
          mask="ssn"
          pii
          label={t(
            "pages.claimsAdditionalUserNotFoundInfo.noMatchFoundSsnLabel"
          )}
          hint=""
          smallLabel={true}
        />
        <InputText
          {...getFunctionalInputProps("employer_fein")}
          inputMode="numeric"
          label={t(
            "pages.claimsAdditionalUserNotFoundInfo.noMatchFoundFeinLabel"
          )}
          mask="fein"
          hint=""
          smallLabel={true}
        />
      </Fieldset>
    </QuestionPage>
  );
};

export default withBenefitsApplication(NoMatchFound);
