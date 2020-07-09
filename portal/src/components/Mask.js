import PropTypes from "prop-types";
import React from "react";

// Deliminate chunks of integers
const maskDeliminatedRegex = {
  ssn: /([*\d]{3})([*\d]{1,2})?([*\d]+)?/,
  fein: /([*\d]{2})([*\d]+)?/,
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
 * Returns the value with additional masking characters
 * @param {string} value
 * @returns {string}
 */
export function maskValue(value, mask) {
  if (maskDeliminatedRegex[mask]) {
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
    const maskedValue = maskValue(evt.target.value, props.mask);

    dispatchChange(maskedValue, evt);
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

  const modifiedInputText = React.cloneElement(field, {
    defaultValue: undefined,
    inputMode: "numeric",
    type: "text",
    value: field.props.value,
    onBlur: handleBlur,
    onChange: field.props.onChange,
  });

  return modifiedInputText;
}

Mask.propTypes = {
  /**
   * Must contain InputText element.
   */
  children: PropTypes.node.isRequired,
  /**
   * The mask type to be applied.
   */
  mask: PropTypes.oneOf(["ssn"]),
};

export default Mask;
