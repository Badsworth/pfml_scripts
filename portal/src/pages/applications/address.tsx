import React, { useEffect } from "react";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import AddressModel from "../../models/Address";
import ConditionalContent from "../../components/ConditionalContent";
import FieldsetAddress from "../../components/FieldsetAddress";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = [
  "claim.has_mailing_address",
  "claim.residential_address.line_1",
  "claim.residential_address.line_2",
  "claim.residential_address.city",
  "claim.residential_address.state",
  "claim.residential_address.zip",
  // Include `mailing_address` so validation error shows for completely empty mailing address.
  // We don't need this for `residential_address` since that defaults to a blank object, rather than null.
  "claim.mailing_address",
  "claim.mailing_address.line_1",
  "claim.mailing_address.line_2",
  "claim.mailing_address.city",
  "claim.mailing_address.sate",
  "claim.mailing_address.zip",
];

export const Address = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );

  const { has_mailing_address } = formState;

  /**
   * When user indicates they have a mailing address,
   * add a blank mailing address so validations are ran against it
   */
  useEffect(() => {
    const existingMailingAddress = formState.mailing_address;
    if (formState.has_mailing_address && !existingMailingAddress) {
      updateFields({ mailing_address: {} });
    }
  }, [formState, updateFields]);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const residentialAddressProps = getFunctionalInputProps(
    "residential_address"
  );
  if (!residentialAddressProps.value) {
    residentialAddressProps.value = new AddressModel({});
  }

  const mailingAddressProps = getFunctionalInputProps("mailing_address");
  if (!mailingAddressProps.value) {
    mailingAddressProps.value = new AddressModel({});
  }

  return (
    <QuestionPage title={t("pages.claimsAddress.title")} onSave={handleSave}>
      <FieldsetAddress
        errors={appLogic.errors}
        label={t("pages.claimsAddress.sectionLabel")}
        hint={t("pages.claimsAddress.hint")}
        {...residentialAddressProps}
      />
      <InputChoiceGroup
        {...getFunctionalInputProps("has_mailing_address")}
        choices={[
          {
            checked: has_mailing_address === false,
            label: t("pages.claimsAddress.choiceYes"),
            value: "false",
          },
          {
            checked: has_mailing_address === true,
            label: t("pages.claimsAddress.choiceNo"),
            value: "true",
          },
        ]}
        label={t("pages.claimsAddress.hasMailingAddressLabel")}
        hint={t("pages.claimsAddress.hasMailingAddressHint")}
        type="radio"
      />
      <ConditionalContent
        fieldNamesClearedWhenHidden={["mailing_address"]}
        getField={getField}
        clearField={clearField}
        updateFields={updateFields}
        visible={has_mailing_address}
      >
        <FieldsetAddress
          errors={appLogic.errors}
          label={t("pages.claimsAddress.mailingAddressLabel")}
          hint={t("pages.claimsAddress.mailingAddressHint")}
          addressType="mailing"
          {...mailingAddressProps}
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

export default withBenefitsApplication(Address);
