import { useState, isValidElement } from "react";
import Link from "next/link";

type option = {
  enabled: boolean;
  text: string;
  type: "button" | "link";
  onClick?: Function;
  href?: string;
};

type Props = {
  options: option[];
};

export default function VerticalMenu({ options }: Props) {
  const [open, setOpen] = useState(false);

  const toggleOpen = () => {
    setOpen(!open);
  };

  const handleOnClick = (event: React.MouseEvent, onClick?: Function) => {
    event.preventDefault();

    onClick && onClick(event);
  };

  const listItems = options.map((option: option) => {
    if (!option.enabled) {
      return (
        <span className="vertical-menu__item vertical-menu__item--disabled">
          {option.text}
        </span>
      );
    }
    if (option.type === "link" && option.href) {
      return (
        <Link href={option.href}>
          <a className="vertical-menu__item vertical-menu__link">
            {option.text}
          </a>
        </Link>
      );
    }
    if (option.type === "button" && option.onClick) {
      return (
        <button
          className="vertical-menu__item vertical-menu__button"
          onClick={(e) => {
            handleOnClick(e, option.onClick);
          }}
          type="button"
        >
          {option.text}
        </button>
      );
    }
    return null;
  });

  return (
    <div className="vertical-menu">
      <button
        className="vertical-menu__icon pfml-icon--vmenu"
        onClick={toggleOpen}
        type="button"
      ></button>

      {open && (
        <ul className="vertical-menu__dropdown">
          {listItems.map((listItem, index) => {
            return isValidElement(listItem) && listItem.type === "span" ? (
              <li key={index}>{listItem}</li>
            ) : (
              <li key={index} onClick={toggleOpen}>
                {listItem}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
