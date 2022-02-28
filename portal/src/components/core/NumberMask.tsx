import Icon from "./Icon";
import React from "react";
import classnames from "classnames";

// Deliminate chunks of integers
const MaskDeliminatedRegex = {
  ssn: /([*\d]{3})([*\d]{1,2})?([*\d]+)?/,
  fein: /([*\d]{2})([*\d]+)?/,
  phone: /([*\d]{3})([*\d]{1,3})?([*\d]+)?/,
  zip: /([*\d]{5})([*\d]+)?/,
} as const;

/**
 * Split value into groups and insert a hyphen deliminator between each
 * @returns {string}
 */
function deliminateRegexGroups(value: string, rx: RegExp) {
  const matches = toDigits(value).match(rx);
  let formattedValue = value;

  if (matches && matches.length > 1) {
    formattedValue = matches
      .slice(1)
      .filter((a) => !!a) // remove undefined groups
      .join("-");
  }

  return formattedValue;
}

/**
 * Remove all non-digits, except masking character (*)
 */
function toDigits(value: string) {
  return value.replace(/[^\d*]/g, "");
}

/**
 * Format a string using fixed-point notation, similar to Number.prototype.toFixed
 * though a decimal is only fixed if the string included a decimal already
 * @param value - A stringified number (i.e. "1234")
 * @param digits - The number of digits to appear after the decimal point
 */
function stringWithFixedDigits(value: string, digits = 2) {
  const decimalRegex = /\.[\d]+$/;
  if (decimalRegex.test(value)) {
    const decimalMatch = value.match(decimalRegex);
    if (decimalMatch && decimalMatch.length > 0) {
      const decimal = decimalMatch[0];
      const fixedDecimalMatch = parseFloat(decimal)
        .toFixed(digits)
        .match(decimalRegex);

      if (fixedDecimalMatch && fixedDecimalMatch.length > 0) {
        return value.replace(decimal, fixedDecimalMatch[0]);
      }
    }
  }

  return value;
}

/**
 * Convert string into a number (positive or negative float or integer)
 */
function toNumber(value: string) {
  const sign = value.charAt(0) === "-" ? -1 : 1;
  const parts = value.split(".");
  // This assumes if the user adds a "." it should be a float. If we want it to
  // evaluate as an integer if there are no digits beyond the decimal, then we
  // can change it.
  const hasDecimal = parts[1] !== undefined;
  if (hasDecimal) {
    const a = toDigits(parts[0]);
    const b = toDigits(parts[1]);
    return sign * parseFloat(`${a}.${b}`);
  } else {
    return sign * parseInt(toDigits(parts[0]));
  }
}

/**
 * Returns the value with additional masking characters
 */
export function maskValue(
  value: string,
  mask: "currency" | "hours" | keyof typeof MaskDeliminatedRegex
) {
  if (mask === "currency" || mask === "hours") {
    // Format number with commas. If the number includes a decimal,
    // ensure it includes two decimal points
    const number = toNumber(value);
    if (number !== undefined && !Number.isNaN(number)) {
      return stringWithFixedDigits(number.toLocaleString("en-US"));
    }

    return value;
  }

  return deliminateRegexGroups(value, MaskDeliminatedRegex[mask]);
}

interface MaskProps {
  children: JSX.Element; // it is an input
  mask: "currency" | "fein" | "hours" | "phone" | "ssn" | "zip";
}

/**
 * Mask component that takes an input field expecting numbers only, and applies a specified mask.
 * Adapted from [CMS design system MaskedField](https://design.cms.gov/components/masked-field).
 * Source code: [Mask](https://github.com/CMSgov/design-system/blob/master/packages/design-system/src/components/TextField/Mask.jsx)
 */
function Mask(props: MaskProps) {
  const field = React.Children.only(props.children);

  /**
   * To avoid a jarring experience for screen readers, we only
   * add/remove characters after the field has been blurred,
   * rather than when the user is typing in the field
   */
  const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    maskAndDispatchChangeFromEvent(event);

    if (field.props.onBlur) {
      field.props.onBlur(event);
    }
  };

  /**
   * To ensure we only submit the masked value, we need to
   * mask the input when the Enter key is pressed
   */
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      maskAndDispatchChangeFromEvent(event);
    }

    if (field.props.onKeyDown) {
      field.props.onKeyDown(event);
    }
  };

  /**
   * Call props.onChange with an argument value in a shape resembling Event so
   * that our form event handlers can manage this field's state just like
   * it does with other InputText fields. We also include the original event
   * for debugging purposes.
   */
  const dispatchChange = (
    value: string,
    originalEvent:
      | React.ChangeEvent<HTMLInputElement>
      | React.FocusEvent<HTMLInputElement>
      | React.KeyboardEvent<HTMLInputElement>
  ) => {
    const target = (originalEvent.target as HTMLInputElement).cloneNode(
      true
    ) as HTMLInputElement; // https://github.com/microsoft/TypeScript/issues/283
    target.value = value;
    field.props.onChange({
      target,
    });
  };

  /**
   * Apply the mask and update the field state
   */
  const maskAndDispatchChangeFromEvent = (
    event:
      | React.ChangeEvent<HTMLInputElement>
      | React.FocusEvent<HTMLInputElement>
      | React.KeyboardEvent<HTMLInputElement>
  ) => {
    const maskedValue = maskValue(
      (event.target as HTMLInputElement).value,
      props.mask
    );
    dispatchChange(maskedValue, event);
  };

  let autoComplete;
  if (field.props.autoComplete) {
    autoComplete = field.props.autoComplete;
  } else if (props.mask === "phone") {
    autoComplete = "tel-national";
  }

  const modifiedInputText = React.cloneElement(field, {
    defaultValue: undefined,
    inputMode:
      props.mask === "currency" || props.mask === "hours"
        ? "decimal"
        : "numeric",
    type: props.mask === "phone" ? "tel" : "text",
    autoComplete,
    value: field.props.value,
    onBlur: handleBlur,
    onChange: field.props.onChange,
    onKeyDown: handleKeyDown,
    className: classnames(field.props.className, {
      "padding-left-0": props.mask === "currency",
    }),
  });

  return (
    <div
      className={classnames({
        "usa-input-group": props.mask === "currency",
      })}
    >
      {props.mask === "currency" && (
        <div className="usa-input-prefix" aria-hidden="true">
          <Icon name="attach_money" />
        </div>
      )}
      {modifiedInputText}
    </div>
  );
}

export default Mask;
