import React, { useState } from "react";
import InputChoice from "./InputChoice";
import InputText from "./InputText";
import { useTranslation } from "../locales/i18n";
import useUniqueId from "../hooks/useUniqueId";

/**
 * This component supports most (not all) InputText props and passes those
 * props directly to InputText. It should not be passed props such as `type`.
 */
interface InputPasswordProps {
  /**
   * HTML input `autocomplete` attribute
   */
  autoComplete?: string;
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg?: React.ReactNode;
  /**
   * Localized example text
   */
  example?: string;
  /**
   * Additional classes to include on the containing form group element
   */
  formGroupClassName?: string;
  /**
   * Localized hint text
   */
  hint?: React.ReactNode;
  /**
   * Additional classes to include on the HTML input
   */
  inputClassName?: string;
  /**
   * Localized field label
   */
  label: React.ReactNode;
  /**
   * Override the label's default text-bold class
   */
  labelClassName?: string;
  /**
   * HTML input `maxlength` attribute
   */
  maxLength?: number;
  /**
   * HTML input `name` attribute
   */
  name: string;
  onBlur?: React.FocusEventHandler<HTMLInputElement>;
  onFocus?: React.FocusEventHandler<HTMLInputElement>;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  /**
   * Enable the smaller label variant
   */
  smallLabel?: boolean;
  /**
   * Change the width of the input field
   */
  width?: "small" | "medium";
}

/**
 * An input that can be toggled between type="password" and type="text".
 */
const InputPassword = (props: InputPasswordProps) => {
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
        aria-controls={inputId}
      />
    </React.Fragment>
  );
};

export default InputPassword;
