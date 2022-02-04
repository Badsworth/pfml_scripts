import { useState, isValidElement } from "react";
import Link from "next/link";
import { LinkProps } from "next/link";

export type Option = {
  enabled: boolean;
  text: string;
  type: "button" | "link";
  onClick?: Function;
  href?: LinkProps["href"];
};

export type Props = {
  options: Option[];
};

export default function ActionMenu({ options }: Props) {
  const [open, setOpen] = useState(false);

  const toggleOpen = () => {
    setOpen(!open);
  };

  const handleOnClick = (onClick?: Function) => (event: React.MouseEvent) => {
    event.preventDefault();
    onClick && onClick(event);
  };

  const listItems = options
    .filter((option) => option.enabled)
    .map((option: Option) => {
      if (!option.enabled) {
        return (
          <span className="action-menu__item action-menu__item--disabled">
            {option.text}
          </span>
        );
      }
      if (option.type === "link" && option.href) {
        return (
          <Link href={option.href}>
            <a className="action-menu__link">{option.text}</a>
          </Link>
        );
      }
      if (option.type === "button" && option.onClick) {
        return (
          <button
            className="action-menu__button"
            onClick={handleOnClick(option.onClick)}
            type="button"
          >
            {option.text}
          </button>
        );
      }
      return null;
    });

  return (
    <div className="action-menu">
      <ul className="action-menu__list">
        {listItems.map((listItem, index) => {
          return isValidElement(listItem) && listItem.type === "span" ? (
            <li className="action-menu__item" key={index}>
              {listItem}
            </li>
          ) : (
            <li className="action-menu__item" key={index} onClick={toggleOpen}>
              {listItem}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
