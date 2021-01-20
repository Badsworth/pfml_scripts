import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import Fieldset from "./Fieldset";
import FormLabel from "./FormLabel";
import InputText from "./InputText";
import PropTypes from "prop-types";
import React from "react";
import StateDropdown from "./StateDropdown";
import { useTranslation } from "../locales/i18n";

/**
 * A fieldset for collecting a user's US address.
 */
const FieldsetAddress = ({ addressType = "residential", ...props }) => {
  const { appErrors, name, onChange, value } = props;
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
        errorMsg={appErrors.fieldErrorMessage(`${name}.line_1`)}
        label={line1Label}
        name={`${name}.line_1`}
        onChange={onChange}
        smallLabel
        value={value.line_1 || ""}
      />

      <InputText
        autoComplete="address-line2"
        errorMsg={appErrors.fieldErrorMessage(`${name}.line_2`)}
        label={line2Label}
        name={`${name}.line_2`}
        onChange={onChange}
        optionalText={t("components.form.optional")}
        smallLabel
        value={value.line_2 || ""}
      />

      <InputText
        autoComplete="address-level2"
        errorMsg={appErrors.fieldErrorMessage(`${name}.city`)}
        label={t("components.fieldsetAddress.cityLabel")}
        name={`${name}.city`}
        onChange={onChange}
        smallLabel
        value={value.city || ""}
      />

      <StateDropdown
        emptyChoiceLabel={t("components.dropdown.emptyChoiceLabel")}
        errorMsg={appErrors.fieldErrorMessage(`${name}.state`)}
        label={t("components.fieldsetAddress.stateLabel")}
        name={`${name}.state`}
        onChange={onChange}
        smallLabel
        value={value.state || ""}
      />

      <InputText
        autoComplete="postal-code"
        errorMsg={appErrors.fieldErrorMessage(`${name}.zip`)}
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

FieldsetAddress.propTypes = {
  /**
   * Error messages which may apply to one of the address fields
   */
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  /**
   * Localized hint text
   */
  hint: PropTypes.string,
  /**
   * Localized label for the entire fieldset
   */
  label: PropTypes.string.isRequired,
  /**
   * Determines which labels to use
   */
  addressType: PropTypes.oneOf(["residential", "mailing"]),
  /**
   * The root HTML name value. Each field will use a name with
   * this as the prefix.
   */
  name: PropTypes.string.isRequired,
  /**
   * Called when any of the fields' value changes. The event `target` will
   * include the formatted ISO 8601 date as its `value`
   */
  onChange: PropTypes.func.isRequired,
  /**
   * Whether or not to use a small label. Default is false.
   */
  smallLabel: PropTypes.bool,
  /**
   * The address value as an object
   */
  value: PropTypes.exact({
    city: PropTypes.string,
    line_1: PropTypes.string,
    line_2: PropTypes.string,
    state: PropTypes.string,
    zip: PropTypes.string,
  }).isRequired,
};

export default FieldsetAddress;
