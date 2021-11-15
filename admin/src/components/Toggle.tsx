import classNames from "classnames";

export type Props = {
  status: boolean;
};

export default function Toggle({ status }: Props) {
  const toggleClasses = classNames({
    toggle: true,
    "toggle--on": status,
    "toggle--off": !status,
  });

  return (
    <span className={toggleClasses} data-testid="toggle">
      {status ? "ON" : "OFF"}
    </span>
  );
}
