import { cloneDeep, get, pick, set } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Heading from "../../components/core/Heading";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import InputText from "../../components/core/InputText";
import Lead from "../../components/core/Lead";
import { PhoneType } from "../../models/BenefitsApplication";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.phone.phone_number", "claim.phone.phone_type"];

/**
 * A form page to capture the worker's phone number.
 */
export const PhoneNumber = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = async () => {
    const requestData = cloneDeep(formState);

    // TODO (CP-1455): Add support for international phone numbers
    set(requestData, "phone.int_code", "1");

    await appLogic.benefitsApplications.update(
      claim.application_id,
      requestData
    );
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const phone_type = get(formState, "phone.phone_type");

  return (
    <QuestionPage
      title={t("pages.claimsPhoneNumber.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsPhoneNumber.sectionLabel")}
      </Heading>

      <Lead>{t("pages.claimsPhoneNumber.lead")}</Lead>

      <InputText
        {...getFunctionalInputProps("phone.phone_number")}
        mask="phone"
        pii
        label={t("pages.claimsPhoneNumber.phoneNumberLabel")}
        hint={t("pages.claimsPhoneNumber.phoneNumberHint")}
        smallLabel
      />

      <InputChoiceGroup
        {...getFunctionalInputProps("phone.phone_type")}
        choices={[
          {
            checked: phone_type === PhoneType.phone,
            label: t("pages.claimsPhoneNumber.choicePhone"),
            value: PhoneType.phone,
          },
          {
            checked: phone_type === PhoneType.cell,
            label: t("pages.claimsPhoneNumber.choiceCell"),
            value: PhoneType.cell,
          },
        ]}
        label={t("pages.claimsPhoneNumber.phoneTypeLabel")}
        type="radio"
        smallLabel
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(PhoneNumber);
