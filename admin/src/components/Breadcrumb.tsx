import Link, { LinkProps } from "next/link";

import { ChevronLeftIcon } from "@heroicons/react/solid";

export type Props = {
  text: string;
  href: LinkProps["href"];
};

export default function Breadcrumb({ text, href }: Props) {
  return (
    <div className="breadcrumb">
      <ChevronLeftIcon className="breadcrumb__icon" />
      <Link href={href}>
        <a className="breadcrumb__link">{text}</a>
      </Link>
    </div>
  );
}
