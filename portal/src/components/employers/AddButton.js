import Button from "../Button";
import PropTypes from "prop-types";
import React from "react";

/**
 * Generic "add" button used on the leave administrator review page to add
 * previous leaves, concurrent leaves and employer benefits.
 */
const AddButton = ({ disabled = false, label, onClick }) => {
  return (
    <Button
      name="add-entry-button"
      onClick={onClick}
      variation="outline"
      disabled={disabled}
    >
      {label}
    </Button>
  );
};

AddButton.propTypes = {
  disabled: PropTypes.bool,
  label: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default AddButton;
