import Link, { LinkProps } from "next/link";

export type Props = {
  text: string;
  href: LinkProps["href"];
};

export default function Breadcrumb({ text, href }: Props) {
  return (
    <div className="breadcrumb">
      <i className="breadcrumb__icon"></i>
      <Link href={href}>
        <a className="breadcrumb__link">{text}</a>
      </Link>
    </div>
  );
}
