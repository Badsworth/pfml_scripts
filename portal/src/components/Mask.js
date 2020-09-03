import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

// Deliminate chunks of integers
const maskDeliminatedRegex = {
  ssn: /([*\d]{3})([*\d]{1,2})?([*\d]+)?/,
  fein: /([*\d]{2})([*\d]+)?/,
};

// Overlays in specific contexts
const maskOverlayContent = {
  currency: "$",
};

/**
 * Split value into groups and insert a hyphen deliminator between each
 * @param {string} value
 * @param {RegExp} rx - Regular expression with capturing groups
 * @returns {string}
 */
function deliminateRegexGroups(value, rx) {
  const matches = toDigits(value).match(rx);
  if (matches && matches.length > 1) {
    value = matches
      .slice(1)
      .filter((a) => !!a) // remove undefined groups
      .join("-");
  }

  return value;
}

/**
 * Remove all non-digits
 * @param {string} value
 * @returns {string}
 */
function toDigits(value) {
  return value.replace(/[^\d]/g, "");
}

/**
 * Format a string using fixed-point notation, similar to Number.prototype.toFixed
 * though a decimal is only fixed if the string included a decimal already
 * @param {string} value - A stringified number (i.e. "1234")
 * @param {number} digits - The number of digits to appear after the decimal point
 * @returns {string}
 */
function stringWithFixedDigits(value, digits = 2) {
  const decimalRegex = /\.[\d]+$/;
  // Check for existing decimal
  const decimal = value.match(decimalRegex);

  if (decimal) {
    const fixedDecimal = parseFloat(decimal)
      .toFixed(digits)
      .match(decimalRegex)[0];

    return value.replace(decimal, fixedDecimal);
  }

  return value;
}

/**
 * Convert string into a number (positive or negative float or integer)
 * @param {string} value
 * @returns {number}
 */
function toNumber(value) {
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
 * @param {string} value
 * @returns {string}
 */
export function maskValue(value, mask) {
  if (mask === "currency") {
    // Format number with commas. If the number includes a decimal,
    // ensure it includes two decimal points
    const number = toNumber(value);
    if (number !== undefined && !Number.isNaN(number)) {
      value = stringWithFixedDigits(number.toLocaleString("en-US"));
    }
  } else if (maskDeliminatedRegex[mask]) {
    value = deliminateRegexGroups(value, maskDeliminatedRegex[mask]);
  }
  return value;
}

/**
 * Mask component that takes an input field and applies a specified mask.
 * Adapted from [CMS design system MaskedField](https://design.cms.gov/components/masked-field).
 * Source code: [Mask](https://github.com/CMSgov/design-system/blob/master/packages/design-system/src/components/TextField/Mask.jsx)
 */
function Mask(props) {
  const field = React.Children.only(props.children);

  /**
   * To avoid a jarring experience for screen readers, we only
   * add/remove characters after the field has been blurred,
   * rather than when the user is typing in the field
   * @param {object} evt
   */
  const handleBlur = (evt) => {
    maskAndDispatchChangeFromEvent(evt);
  };

  /**
   * To ensure we only submit the masked value, we need to
   * mask the input when the Enter key is pressed
   * @param {object} evt
   */
  const handleKeyDown = (evt) => {
    if (evt.key === "Enter") {
      maskAndDispatchChangeFromEvent(evt);
    }
  };

  /**
   * Call props.onChange with an argument value in a shape resembling Event so
   * that our form event handlers can manage this field's state just like
   * it does with other InputText fields. We also include the original event
   * for debugging purposes.
   * @param {string} value - the masked SSN string
   * @param {SyntheticEvent} originalEvent - Original event that triggered this change
   */
  const dispatchChange = (value, originalEvent) => {
    field.props.onChange({
      _originalEvent: originalEvent,
      target: {
        name: field.props.name,
        type: "text",
        value,
      },
    });
  };

  /**
   * Apply the mask and update the field state
   * @param {object} evt
   */
  const maskAndDispatchChangeFromEvent = (evt) => {
    const maskedValue = maskValue(evt.target.value, props.mask);

    dispatchChange(maskedValue, evt);
  };

  const modifiedInputText = React.cloneElement(field, {
    defaultValue: undefined,
    inputMode: "numeric",
    type: "text",
    value: field.props.value,
    onBlur: handleBlur,
    onChange: field.props.onChange,
    onKeyDown: handleKeyDown,
    className: classnames(field.props.className, {
      "c-inputtext-field--currency": props.mask === "currency",
    }),
  });

  // UI overlayed on top of a field to support certain masks
  const maskOverlay = maskOverlayContent[props.mask] ? (
    <div className={`c-inputtext-mask__before--${props.mask}`}>
      {maskOverlayContent[props.mask]}
    </div>
  ) : null;

  return (
    <div
      className={classnames({
        "c-inputtext-mask--currency": props.mask === "currency",
      })}
    >
      {maskOverlay}
      {modifiedInputText}
    </div>
  );
}

Mask.propTypes = {
  /**
   * Must contain InputText element.
   */
  children: PropTypes.node.isRequired,
  /**
   * The mask type to be applied.
   */
  mask: PropTypes.oneOf(["currency", "fein", "ssn"]),
};

export default Mask;
