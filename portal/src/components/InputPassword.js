import React, { useState } from "react";
import InputChoice from "./InputChoice";
import InputText from "./InputText";
import PropTypes from "prop-types";
import { useTranslation } from "../locales/i18n";
import useUniqueId from "../hooks/useUniqueId";

/**
 * An input that can be toggled between type="password" and type="text".
 */
const InputPassword = (props) => {
  const inputId = useUniqueId("InputPassword");
  const [showPassword, setShowPassword] = useState(false);

  const { t } = useTranslation();

  return (
    <React.Fragment>
      <InputText
        {...props}
        type={showPassword ? "text" : "password"}
        inputId={inputId}
      />
      <InputChoice
        label={t("components.inputPassword.toggleLabel")}
        name={`${inputId}-toggle`}
        value={showPassword ? "text" : "password"}
        onChange={() => setShowPassword(!showPassword)}
        ariaControls={inputId}
      />
    </React.Fragment>
  );
};

/**
 * This component supports most (not all) InputText.propTypes and passes those
 * props directly to InputText. It should not be passed props such as `type`.
 */
InputPassword.propTypes = {
  /**
   * HTML input `autocomplete` attribute
   */
  autoComplete: PropTypes.string,
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized example text
   */
  example: PropTypes.string,
  /**
   * Additional classes to include on the containing form group element
   */
  formGroupClassName: PropTypes.string,
  /**
   * Localized hint text
   */
  hint: PropTypes.node,
  /**
   * Additional classes to include on the HTML input
   */
  inputClassName: PropTypes.string,
  /**
   * Localized field label
   */
  label: PropTypes.node.isRequired,
  /**
   * Override the label's default text-bold class
   */
  labelClassName: PropTypes.string,
  /**
   * HTML input `maxlength` attribute
   */
  maxLength: PropTypes.string,
  /**
   * HTML input `name` attribute
   */
  name: PropTypes.string.isRequired,
  /**
   * HTML input `onBlur` attribute
   */
  onBlur: PropTypes.func,
  /**
   * HTML input `onFocus` attribute
   */
  onFocus: PropTypes.func,
  /**
   * HTML input `onChange` attribute
   */
  onChange: PropTypes.func,
  /**
   * Enable the smaller label variant
   */
  smallLabel: PropTypes.bool,
  /**
   * Change the width of the input field
   */
  width: PropTypes.oneOf(["small", "medium"]),
};

export default InputPassword;
