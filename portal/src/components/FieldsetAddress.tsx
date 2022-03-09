import Fieldset from "./core/Fieldset";
import FormLabel from "./core/FormLabel";
import InputText from "./core/InputText";
import React from "react";
import StateDropdown from "./core/StateDropdown";
import findErrorMessageForField from "../utils/findErrorMessageForField";
import { useTranslation } from "../locales/i18n";

type AddressFieldNames = "city" | "line_1" | "line_2" | "state" | "zip";

interface FieldsetAddressProps {
  /**
   * Error messages which may apply to one of the address fields
   */
  errors: Error[];
  /**
   * Localized hint text
   */
  hint?: string;
  /**
   * Localized label for the entire fieldset
   */
  label: string;
  /**
   * Determines which labels to use
   */
  addressType?: "residential" | "mailing";
  /**
   * The root HTML name value. Each field will use a name with
   * this as the prefix.
   */
  name: string;
  /**
   * Called when any of the fields' value changes. The event `target` will
   * include the formatted ISO 8601 date as its `value`
   */
  onChange: React.ChangeEventHandler<HTMLSelectElement | HTMLInputElement>;
  /**
   * Whether or not to use a small label. Default is false.
   */
  smallLabel?: boolean;
  /**
   * The address value as an object
   */
  value: { [key in AddressFieldNames]: string | null };
}

/**
 * A fieldset for collecting a user's US address.
 */
const FieldsetAddress = ({
  addressType = "residential",
  ...props
}: FieldsetAddressProps) => {
  const { errors, name, onChange, value } = props;
  const { t } = useTranslation();

  const line1Label = t("components.fieldsetAddress.line1Label", {
    context: addressType,
  });
  const line2Label = t("components.fieldsetAddress.line2Label", {
    context: addressType,
  });

  return (
    <Fieldset>
      <FormLabel component="legend" hint={props.hint} small={props.smallLabel}>
        {props.label}
      </FormLabel>

      <InputText
        autoComplete="address-line1"
        errorMsg={findErrorMessageForField(errors, `${name}.line_1`)}
        label={line1Label}
        name={`${name}.line_1`}
        onChange={onChange}
        smallLabel
        value={value.line_1 || ""}
      />

      <InputText
        autoComplete="address-line2"
        errorMsg={findErrorMessageForField(errors, `${name}.line_2`)}
        label={line2Label}
        name={`${name}.line_2`}
        onChange={onChange}
        optionalText={t("components.form.optional")}
        smallLabel
        value={value.line_2 || ""}
      />

      <InputText
        autoComplete="address-level2"
        errorMsg={findErrorMessageForField(errors, `${name}.city`)}
        label={t("components.fieldsetAddress.cityLabel")}
        name={`${name}.city`}
        onChange={onChange}
        smallLabel
        value={value.city || ""}
      />

      <StateDropdown
        emptyChoiceLabel={t("components.dropdown.emptyChoiceLabel")}
        errorMsg={findErrorMessageForField(errors, `${name}.state`)}
        label={t("components.fieldsetAddress.stateLabel")}
        name={`${name}.state`}
        onChange={onChange}
        smallLabel
        value={value.state || ""}
      />

      <InputText
        autoComplete="postal-code"
        errorMsg={findErrorMessageForField(errors, `${name}.zip`)}
        inputMode="numeric"
        label={t("components.fieldsetAddress.zipLabel")}
        mask="zip"
        name={`${name}.zip`}
        onChange={onChange}
        smallLabel
        value={value.zip || ""}
        width="medium"
      />
    </Fieldset>
  );
};

export default FieldsetAddress;
