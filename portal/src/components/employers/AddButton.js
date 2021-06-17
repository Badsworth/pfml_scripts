import Button from "../Button";
import PropTypes from "prop-types";
import React from "react";

/**
 * Generic "add" button used on the leave administrator review page to add
 * previous leaves, concurrent leaves and employer benefits.
 */
const AddButton = (props) => {
  return (
    <Button
      name="add-entry-button"
      onClick={props.onClick}
      variation="outline"
      disabled={props.disabled}
    >
      {props.label}
    </Button>
  );
};

AddButton.propTypes = {
  disabled: PropTypes.bool.isRequired,
  label: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default AddButton;
