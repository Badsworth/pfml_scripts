import { CheckIcon } from "@heroicons/react/solid";
import React from "react";
import classNames from "classnames";

export type Props = {
  className?: string;
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  disabled?: boolean;
};

const CheckBox = ({
  className = "",
  checked,
  onChange,
  disabled = false,
}: Props) => {
  return (
    <span
      className={classNames("checkbox", {
        "checkbox--checked": checked,
        "checkbox--disabled": disabled,
      })}
    >
      {checked && <CheckIcon className="checkbox-icon" />}
      <input
        type="checkbox"
        className={className}
        checked={checked}
        onChange={onChange}
        disabled={disabled}
      />
    </span>
  );
};

export default CheckBox;
