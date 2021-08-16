import React, { useEffect } from "react";
import AddressModel from "../../models/Address";
import BenefitsApplication from "../../models/BenefitsApplication";
import ConditionalContent from "../../components/ConditionalContent";
import FieldsetAddress from "../../components/FieldsetAddress";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

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
  "claim.mailing_address.state",
  "claim.mailing_address.zip",
];

export const Address = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
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
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const residentialAddressProps = getFunctionalInputProps(
    "residential_address"
  );
  if (!residentialAddressProps.value) {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    residentialAddressProps.value = new AddressModel();
  }

  const mailingAddressProps = getFunctionalInputProps("mailing_address");
  if (!mailingAddressProps.value) {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    mailingAddressProps.value = new AddressModel();
  }

  return (
    <QuestionPage title={t("pages.claimsAddress.title")} onSave={handleSave}>
      <FieldsetAddress
        appErrors={appLogic.appErrors}
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
          appErrors={appLogic.appErrors}
          label={t("pages.claimsAddress.mailingAddressLabel")}
          hint={t("pages.claimsAddress.mailingAddressHint")}
          addressType="mailing"
          {...mailingAddressProps}
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

Address.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withBenefitsApplication(Address);
