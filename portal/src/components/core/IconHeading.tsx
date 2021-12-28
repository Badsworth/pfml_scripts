import Heading from "./Heading";
import Icon from "./Icon";
import React from "react";
import classnames from "classnames";

interface IconHeadingProps {
  children: React.ReactNode[] | React.ReactNode;
  name: string;
}

const IconHeading = ({ children, name }: IconHeadingProps) => {
  /**
   * Using name to determine correct flex
   * and color settings
   */
  const styles: { [iconName: string]: { color: string; flexAlign: string } } = {
    check_circle: { color: "text-green", flexAlign: "flex-align-start" },
    cancel: { color: "text-red", flexAlign: "flex-align-center" },
  };

  const { color, flexAlign } = styles[name];

  return (
    <Heading
      className={classnames("display-flex", "flex-row", flexAlign)}
      level="2"
      size="3"
    >
      <Icon
        className={classnames("margin-right-1", "flex-auto", color)}
        name={name}
        fill="currentColor"
        size={3}
      />
      <span className="flex-1">{children}</span>
    </Heading>
  );
};

export default IconHeading;
