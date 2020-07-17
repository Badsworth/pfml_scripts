import Claim, {
  PaymentPreference,
  PaymentPreferenceMethod,
} from "../../models/Claim";
import ConditionalContent from "../../components/ConditionalContent";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import get from "lodash/get";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = ["claim.temp.payment_preferences[0]"];

const PaymentMethod = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const handleInputChange = useHandleInputChange(updateFields);
  const paymentPreference = new PaymentPreference(
    get(formState, "temp.payment_preferences[0]")
  );

  const handleSave = () =>
    props.appLogic.updateClaim(props.claim.application_id, formState);

  return (
    <QuestionPage
      title={t("pages.claimsPaymentMethod.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        choices={[
          {
            checked:
              paymentPreference.payment_method === PaymentPreferenceMethod.ach,
            label: t("pages.claimsPaymentMethod.choiceAch"),
            hint: t("pages.claimsPaymentMethod.choiceHintAch"),
            value: PaymentPreferenceMethod.ach,
          },
          {
            checked:
              paymentPreference.payment_method ===
              PaymentPreferenceMethod.debit,
            label: t("pages.claimsPaymentMethod.choiceDebit"),
            value: PaymentPreferenceMethod.debit,
          },
        ]}
        label={t("pages.claimsPaymentMethod.sectionLabel")}
        name="temp.payment_preferences[0].payment_method"
        onChange={handleInputChange}
        type="radio"
      />

      <ConditionalContent
        visible={
          paymentPreference.payment_method === PaymentPreferenceMethod.ach
        }
      >
        <Fieldset>
          <FormLabel component="legend">
            {t("pages.claimsPaymentMethod.achSectionLabel")}
          </FormLabel>
          <Lead>{t("pages.claimsPaymentMethod.achLead")}</Lead>

          <InputText
            name="temp.payment_preferences[0].account_details.routing_number"
            value={valueWithFallback(
              paymentPreference.account_details.routing_number
            )}
            label={t("pages.claimsPaymentMethod.routingNumberLabel")}
            hint={t("pages.claimsPaymentMethod.routingNumberHint")}
            onChange={handleInputChange}
            inputMode="numeric"
            smallLabel
            width="medium"
          />

          <InputText
            name="temp.payment_preferences[0].account_details.account_number"
            value={valueWithFallback(
              paymentPreference.account_details.account_number
            )}
            label={t("pages.claimsPaymentMethod.accountNumberLabel")}
            onChange={handleInputChange}
            inputMode="numeric"
            smallLabel
          />
        </Fieldset>
      </ConditionalContent>

      <ConditionalContent
        visible={
          paymentPreference.payment_method === PaymentPreferenceMethod.debit
        }
      >
        <Fieldset>
          <FormLabel component="legend">
            {t("pages.claimsPaymentMethod.debitSectionLabel")}
          </FormLabel>

          <InputText
            name="temp.payment_preferences[0].destination_address.line_1"
            value={valueWithFallback(
              paymentPreference.destination_address.line_1
            )}
            label={t("pages.claimsPaymentMethod.addressLine1Label")}
            onChange={handleInputChange}
            autoComplete="address-line1"
            smallLabel
          />

          <InputText
            name="temp.payment_preferences[0].destination_address.line_2"
            value={valueWithFallback(
              paymentPreference.destination_address.line_2
            )}
            label={t("pages.claimsPaymentMethod.addressLine2Label")}
            onChange={handleInputChange}
            optionalText={t("components.form.optionalText")}
            autoComplete="address-line2"
            smallLabel
          />

          <InputText
            name="temp.payment_preferences[0].destination_address.city"
            value={valueWithFallback(
              paymentPreference.destination_address.city
            )}
            label={t("pages.claimsPaymentMethod.addressCityLabel")}
            onChange={handleInputChange}
            autoComplete="address-level2"
            smallLabel
          />

          <InputText
            name="temp.payment_preferences[0].destination_address.state"
            value={valueWithFallback(
              paymentPreference.destination_address.state
            )}
            label={t("pages.claimsPaymentMethod.addressStateLabel")}
            onChange={handleInputChange}
            autoComplete="address-level1"
            smallLabel
          />

          <InputText
            name="temp.payment_preferences[0].destination_address.zip"
            value={valueWithFallback(paymentPreference.destination_address.zip)}
            label={t("pages.claimsPaymentMethod.addressZipLabel")}
            onChange={handleInputChange}
            autoComplete="postal-code"
            inputMode="numeric"
            smallLabel
            width="medium"
          />
        </Fieldset>
      </ConditionalContent>
    </QuestionPage>
  );
};

PaymentMethod.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(PaymentMethod);
