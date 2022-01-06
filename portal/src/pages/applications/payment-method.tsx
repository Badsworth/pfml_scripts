import {
  BankAccountType,
  PaymentPreferenceMethod,
} from "../../models/PaymentPreference";
import { cloneDeep, get, pick, set } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Alert from "../../components/core/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../../components/core/Details";
import Fieldset from "../../components/core/Fieldset";
import FormLabel from "../../components/core/FormLabel";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import InputText from "../../components/core/InputText";
import Lead from "../../components/core/Lead";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import { isPotentialRoutingNumber } from "../../utils/isPotentialRoutingNumber";
import routes from "../../routes";
import tracker from "src/services/tracker";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

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

export const PaymentMethod = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  // TODO(Portal-1001): - Remove featureFlag
  const taxWithholdingEnabled = isFeatureEnabled("claimantShowTaxWithholding");

  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );
  const [displayAccountNumWarning, setDisplayAccountNumWarning] =
    React.useState(false);

  const bank_account_type = get(formState, bankAccountTypeField);
  const payment_method = get(formState, paymentMethodField);
  const requestData = cloneDeep(formState);

  const handleSubmit = async () => {
    if (payment_method !== PaymentPreferenceMethod.ach) {
      set(requestData, routingNumberField, null);
      set(requestData, bankAccountTypeField, null);
      set(requestData, accountNumberField, null);
    }
    await appLogic.benefitsApplications.submitPaymentPreference(
      claim.application_id,
      requestData
    );
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  /**
   * Previously we received a lot of account numbers that were invalid bc they were actually routing numbers.
   * So, here we are checking for that to guide the user.
   */
  const validateAccountNumber = React.useCallback((accountNum) => {
    const potientialRouting = isPotentialRoutingNumber(accountNum);
    setDisplayAccountNumWarning(potientialRouting);
    if (potientialRouting === true) {
      tracker.trackEvent(
        "Claimant potentially entered a routing number in place of account number."
      );
    }
  }, []);

  const handleAccountNumberChange = (
    evt: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { onChange } = getFunctionalInputProps(accountNumberField);
    onChange(evt);
    validateAccountNumber(evt.target.value);
  };

  return (
    <QuestionPage
      continueButtonLabel={
        taxWithholdingEnabled
          ? t("pages.claimsPaymentMethod.submitPayment")
          : t("pages.claimsPaymentMethod.submitPart2Button")
      }
      onSave={handleSubmit}
      title={t("pages.claimsPaymentMethod.title")}
    >
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
            onChange={handleAccountNumberChange}
            pii
          />
          <ConditionalContent visible={displayAccountNumWarning}>
            <Alert state="warning" autoWidth>
              {t("pages.claimsPaymentMethod.accountNumberWarning")}
            </Alert>
          </ConditionalContent>
          <InputChoiceGroup
            {...getFunctionalInputProps("payment_preference.bank_account_type")}
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
        {taxWithholdingEnabled ? (
          <Trans
            i18nKey="pages.claimsPaymentMethod.warning"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
        ) : (
          <Trans
            i18nKey="pages.claimsPaymentMethod.partTwoNextSteps"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
              "benefits-guide-link": (
                <a
                  href={routes.external.massgov.benefitsGuide}
                  target="_blank"
                  rel="noreferrer noopener"
                />
              ),
            }}
          />
        )}
      </div>
    </QuestionPage>
  );
};

export default withBenefitsApplication(PaymentMethod);