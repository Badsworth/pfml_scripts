import BenefitsApplication, {
  PhoneType,
} from "../../models/BenefitsApplication";
import { cloneDeep, get, pick, set } from "lodash";
import Heading from "../../components/Heading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.phone.phone_number", "claim.phone.phone_type"];

/**
 * A form page to capture the worker's phone number.
 */
export const PhoneNumber = (props) => {
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
    appErrors: appLogic.appErrors,
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

PhoneNumber.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(PhoneNumber);
