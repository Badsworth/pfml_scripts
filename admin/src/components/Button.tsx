import React from "react";
import classNames from "classnames";

type Props = {
  additionalClasses?: string[];
  callback: Function;
  children?: React.ReactNode;
};

const Button = ({ additionalClasses = [], callback, children }: Props) => {
  const handleOnClick = (event: React.MouseEvent) => {
    event.preventDefault();

    callback(event);
  };

  const classes = classNames([...additionalClasses, "btn"]);

  return (
    <button className={classes} onClick={handleOnClick}>
      {children}
    </button>
  );
};

export default Button;
