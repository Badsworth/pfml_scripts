import {
  BankAccountType,
  PaymentPreferenceMethod,
} from "../../models/PaymentPreference";
import { cloneDeep, get, pick, set } from "lodash";
import BackButton from "../../components/BackButton";
import BenefitsApplication from "../../models/BenefitsApplication";
import Button from "../../components/Button";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../../components/Details";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

const bankAccountTypeField = "payment_preference.bank_account_type";
const routingNumberField = "payment_preference.routing_number";
const accountNumberField = "payment_preference.account_number";
const paymentMethodField = "payment_preference.payment_method";

export const fields = [
  `claim.${paymentMethodField}`,
  `claim.${accountNumberField}`,
  `claim.${bankAccountTypeField}`,
  `claim.${routingNumberField}`,
];

export const PaymentMethod = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );

  const bank_account_type = get(formState, bankAccountTypeField);
  const payment_method = get(formState, paymentMethodField);
  const requestData = cloneDeep(formState);

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    if (payment_method !== PaymentPreferenceMethod.ach) {
      set(requestData, routingNumberField, null);
      set(requestData, bankAccountTypeField, null);
      set(requestData, accountNumberField, null);
    }
    await appLogic.benefitsApplications.submitPaymentPreference(
      claim.application_id,
      requestData
    );
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <React.Fragment>
      <BackButton />
      <form onSubmit={handleSubmit} className="usa-form" method="post">
        <Title small>{t("pages.claimsPaymentMethod.title")}</Title>
        <InputChoiceGroup
          {...getFunctionalInputProps("payment_preference.payment_method")}
          choices={[
            {
              checked: payment_method === PaymentPreferenceMethod.ach,
              label: t("pages.claimsPaymentMethod.choiceAch"),
              hint: t("pages.claimsPaymentMethod.choiceHintAch"),
              value: PaymentPreferenceMethod.ach,
            },
            {
              checked: payment_method === PaymentPreferenceMethod.check,
              label: t("pages.claimsPaymentMethod.choiceCheck"),
              hint: t("pages.claimsPaymentMethod.choiceHintCheck"),
              value: PaymentPreferenceMethod.check,
            },
          ]}
          label={t("pages.claimsPaymentMethod.sectionLabel")}
          type="radio"
          hint={
            <React.Fragment>
              <p>{t("pages.claimsPaymentMethod.sectionLabelHint")}</p>
              <Details
                label={t("pages.claimsPaymentMethod.whenWillIGetPaidLabel")}
              >
                <div className="margin-bottom-5">
                  <Trans i18nKey="pages.claimsPaymentMethod.whenWillIGetPaidDetails" />
                </div>
              </Details>
            </React.Fragment>
          }
        />

        <ConditionalContent
          fieldNamesClearedWhenHidden={[
            "payment_preference.account_number",
            "payment_preference.bank_account_type",
            "payment_preference.routing_number",
          ]}
          getField={getField}
          updateFields={updateFields}
          clearField={clearField}
          visible={payment_method === PaymentPreferenceMethod.ach}
        >
          <Fieldset>
            <FormLabel component="legend">
              {t("pages.claimsPaymentMethod.achSectionLabel")}
            </FormLabel>
            <Lead>{t("pages.claimsPaymentMethod.achLead")}</Lead>

            <InputText
              {...getFunctionalInputProps("payment_preference.routing_number")}
              label={t("pages.claimsPaymentMethod.routingNumberLabel")}
              hint={t("pages.claimsPaymentMethod.routingNumberHint")}
              inputMode="numeric"
              smallLabel
              width="medium"
              pii
            />

            <InputText
              {...getFunctionalInputProps("payment_preference.account_number")}
              label={t("pages.claimsPaymentMethod.accountNumberLabel")}
              inputMode="numeric"
              smallLabel
              pii
            />

            <InputChoiceGroup
              {...getFunctionalInputProps(
                "payment_preference.bank_account_type"
              )}
              choices={[
                {
                  checked: bank_account_type === BankAccountType.checking,
                  label: t("pages.claimsPaymentMethod.achTypeChecking"),
                  value: BankAccountType.checking,
                },
                {
                  checked: bank_account_type === BankAccountType.savings,
                  label: t("pages.claimsPaymentMethod.achTypeSavings"),
                  value: BankAccountType.savings,
                },
              ]}
              label={t("pages.claimsPaymentMethod.achTypeLabel")}
              type="radio"
              smallLabel
            />
          </Fieldset>
        </ConditionalContent>
        <div className="margin-top-6 margin-bottom-2">
          <Trans
            i18nKey="pages.claimsPaymentMethod.partTwoNextSteps"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
        </div>
        <Button
          className="margin-top-4"
          onClick={handleSubmit}
          type="submit"
          loading={handleSubmit.isThrottled}
        >
          {t("pages.claimsPaymentMethod.submitPart2Button")}
        </Button>
      </form>
    </React.Fragment>
  );
};

PaymentMethod.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withBenefitsApplication(PaymentMethod);
