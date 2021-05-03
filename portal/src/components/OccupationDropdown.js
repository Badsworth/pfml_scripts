/* eslint sort-keys: "error" */
import Dropdown from "./Dropdown";
import PropTypes from "prop-types";
import React from "react";

/**
 * A dropdown of occupations
 */
const OccupationDropdown = (props) => {
  return (
    <Dropdown
      autoComplete="address-level1"
      choices={occupationDropdownChoices}
      {...props}
    />
  );
};

OccupationDropdown.propTypes = {
  /**
   * Localized label for the initially selected option when no value is set
   */
  emptyChoiceLabel: PropTypes.string.isRequired,
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized hint text
   */
  hint: PropTypes.node,
  /**
   * Additional classes to include on the HTML input
   */
  inputClassName: PropTypes.string,
  /**
   * Localized label
   */
  label: PropTypes.node.isRequired,
  /**
   * HTML input `name` attribute */
  name: PropTypes.string.isRequired,
  /**
   * HTML input `onChange` attribute
   */
  onChange: PropTypes.func,
  /**
   * Localized text indicating this field is optional
   */
  optionalText: PropTypes.node,
  /**
   * Enable the smaller label variant
   */
  smallLabel: PropTypes.bool,
  /** The `value` of the selected choice */
  value: PropTypes.string,
};

// All Occupation
const occupationDropdownChoices = [];

export default OccupationDropdown;
