/* eslint-disable jsx-a11y/no-static-element-interactions, jsx-a11y/click-events-have-key-events */
import Link from "next/link";
import React from "react";
import classnames from "classnames";

interface ButtonLinkProps {
  disabled?: boolean;
  children: React.ReactNode;
  "aria-label"?: string;
  className?: string;
  href: string;
  variation?: "outline" | "secondary" | "accent-cool" | "unstyled";
  inversed?: boolean;
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
}

/**
 * Next.js [`Link`](https://nextjs.org/docs/api-reference/next/link)
 * styled as a button. Provides client-side transitions between routes.
 */
const ButtonLink = (props: ButtonLinkProps) => {
  const classes = classnames(
    "usa-button",
    props.className,
    props.variation ? `usa-button--${props.variation}` : "",
    {
      "usa-button--inverse": props.inversed,
      // This is weird, but we need this so that the inversed styling
      // kicks in when the variation is unstyled
      "usa-button--outline": props.inversed && props.variation === "unstyled",
    },
    { disabled: props.disabled }
  );

  if (props.disabled) {
    return (
      <button
        type="button"
        className={classes}
        aria-label={props["aria-label"]}
        disabled
      >
        {props.children}
      </button>
    );
  }

  return (
    <Link href={props.href}>
      <a
        className={classes}
        aria-label={props["aria-label"]}
        onClick={props.onClick}
      >
        {props.children}
      </a>
    </Link>
  );
};

export default ButtonLink;
