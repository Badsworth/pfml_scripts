import React from "react";
import classNames from "classnames";

export type Props = {
  className?: string;
  onClick: Function;
  disabled?: boolean;
  children?: React.ReactNode;
};

const Button = ({
  className = "",
  onClick,
  children,
  disabled = false,
}: Props) => {
  const handleOnClick = (event: React.MouseEvent) => {
    event.preventDefault();
    onClick(event);
  };

  const classes = classNames([...className?.split(" "), "btn"]);

  return (
    <button
      type="button"
      className={classes}
      onClick={handleOnClick}
      data-testid="button"
      disabled={disabled}
    >
      {children}
    </button>
  );
};

export default Button;
