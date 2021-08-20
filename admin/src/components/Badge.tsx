import classNames from "classnames";

export default function Badge({ type = "employee" }) {
  const badgeClasses = classNames({
    "features-badge": true,
    [`features-badge--${type}`]: true,
  });

  const types: { [index: string]: any } = {
    employee: "Employee",
    employer: "Employer",
    "leave-admin": "Leave Admin",
  };

  return <span className={badgeClasses}>{types[type]}</span>;
}
