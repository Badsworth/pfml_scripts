import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Fieldset from "../../components/core/Fieldset";
import FormLabel from "../../components/core/FormLabel";
import InputText from "../../components/core/InputText";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = [
  "claim.first_name",
  "claim.middle_name",
  "claim.last_name",
];

export const Name = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage title={t("pages.claimsName.title")} onSave={handleSave}>
      <Fieldset>
        <FormLabel component="legend" hint={t("pages.claimsName.lead")}>
          {t("pages.claimsName.sectionLabel")}
        </FormLabel>
        <InputText
          {...getFunctionalInputProps("first_name")}
          label={t("pages.claimsName.firstNameLabel")}
          smallLabel
        />
        <InputText
          {...getFunctionalInputProps("middle_name")}
          label={t("pages.claimsName.middleNameLabel")}
          optionalText={t("components.form.optional")}
          smallLabel
        />
        <InputText
          {...getFunctionalInputProps("last_name")}
          label={t("pages.claimsName.lastNameLabel")}
          smallLabel
        />
      </Fieldset>
    </QuestionPage>
  );
};

export default withBenefitsApplication(Name);
