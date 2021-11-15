import classNames from "classnames";

export type Props = {
  status: boolean;
};

const StatusIcon = ({ status }: Props) => {
  const iconClasses = classNames({
    statusicon: true,
    "statusicon--enabled": status,
    "statusicon--disabled": !status,
  });

  return <span className={iconClasses} data-testid="status-icon"></span>;
};

export default StatusIcon;
