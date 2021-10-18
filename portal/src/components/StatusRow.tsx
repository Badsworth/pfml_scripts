import Heading from "./Heading";
import React from "react";
import classnames from "classnames";

interface StatusRowProps {
  className?: string;
  children: React.ReactNode;
  label: React.ReactNode;
}

const StatusRow = ({ className = "", children, label }: StatusRowProps) => {
  const classes = classnames(`margin-bottom-2 padding-bottom-2`, className);

  return (
    <div className={classes}>
      <Heading level="3" size="4" className="margin-bottom-1">
        {label}
      </Heading>
      {children}
    </div>
  );
};

export default StatusRow;
