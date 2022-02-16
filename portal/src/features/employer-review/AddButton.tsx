import Button from "../../components/core/Button";
import React from "react";

interface AddButtonProps {
  disabled?: boolean;
  label: string;
  onClick: React.MouseEventHandler<HTMLButtonElement>;
}

/**
 * Generic "add" button used on the leave administrator review page to add
 * previous leaves, concurrent leaves and employer benefits.
 */
const AddButton = ({ disabled = false, label, onClick }: AddButtonProps) => {
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

export default AddButton;
