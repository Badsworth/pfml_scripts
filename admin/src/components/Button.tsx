import React from "react";
import classNames from "classnames";

type Props = {
  additionalClasses?: string[];
  onClick: Function;
  children?: React.ReactNode;
};

const Button = ({ additionalClasses = [], onClick, children }: Props) => {
  const handleOnClick = (event: React.MouseEvent) => {
    event.preventDefault();

    onClick(event);
  };

  const classes = classNames([...additionalClasses, "btn"]);

  return (
    <button type="button" className={classes} onClick={handleOnClick}>
      {children}
    </button>
  );
};

export default Button;
