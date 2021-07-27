import classNames from "classnames";

type Props = {
  status: boolean;
};

export default function Toggle({ status }: Props) {
  const toggleClasses = classNames({
    toggle: true,
    "toggle--on": status,
    "toggle--off": !status,
  });

  return <span className={toggleClasses}>{status ? "ON" : "OFF"}</span>;
}
