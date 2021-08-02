import { useState } from "react";
import classNames from "classnames";

export default function VerticalMenu({
  options,
  selected,
}: {
  options: string[];
  selected: string;
}) {
  const [open, setOpen] = useState(false);

  const toggleOpen = () => {
    setOpen(!open);
  };

  const enableClasses = "menu__item menu__item--enabled";
  const disableClasses = "menu__item menu__item--disabled";

  return (
    <div className="menu">
      <button
        className="menu__icon pfml-icon--vmenu"
        onClick={toggleOpen}
      ></button>

      {open && (
        <ul className="menu__dropdown">
          {options.map((option: string, index: number) => {
            return (
              <li
                key={index}
                className={selected !== option ? enableClasses : disableClasses}
              >
                {option}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
