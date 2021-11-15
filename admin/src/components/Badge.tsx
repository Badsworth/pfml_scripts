import classNames from "classnames";

export type Props = {
  type?: "employee" | "employer" | "leave-admin";
};

const Badge = ({ type = "employee" }: Props) => {
  const badgeClasses = classNames({
    "features-badge": true,
    [`features-badge--${type}`]: true,
  });

  const types: { [index: string]: any } = {
    employee: "Employee",
    employer: "Employer",
    "leave-admin": "Leave Admin",
  };

  return (
    <span className={badgeClasses} data-testid="badge">
      {types[type]}
    </span>
  );
};

export default Badge;
