import classNames from "classnames";

const StatusIcon = function ({ status }: { status: boolean }) {
  const iconClasses = classNames({
    statusicon: true,
    "statusicon--enabled": status,
    "statusicon--disabled": !status,
  });

  return <span className={iconClasses}></span>;
};

export default StatusIcon;
