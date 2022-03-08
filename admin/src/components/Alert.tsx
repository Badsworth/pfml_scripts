import * as heroIcons from "@heroicons/react/solid";

import React, { useState } from "react";

export type Props = {
  type?: "warn" | "success" | "info" | "error" | "neutral";
  closeable?: boolean;
  children: string;
  onClose?: Function;
};

const Alert = ({
  type = "neutral",
  closeable = false,
  onClose = () => {},
  children,
}: Props) => {
  const [showAlert, setAlert] = useState(true);

  const closeAlert = (event: React.MouseEvent) => {
    event.preventDefault();

    setAlert(false);
    onClose(event);
  };

  const DismissIcon = heroIcons["XIcon"];
  let Icon;
  switch (type) {
    case "warn":
      Icon = heroIcons["ExclamationIcon"];
      break;

    case "success":
      Icon = heroIcons["CheckCircleIcon"];
      break;

    case "info":
      Icon = heroIcons["InformationCircleIcon"];
      break;

    case "error":
      Icon = heroIcons["ExclamationCircleIcon"];
      break;

    default:
      Icon = null;
      break;
  }

  if (showAlert) {
    return (
      <div className={`alert alert--${type}`} data-testid="alert-container">
        {Icon && <Icon className={`alert__icon alert__icon--${type}`} />}
        <div className="alert__text" data-testid="alert-text">
          {children}
        </div>
        {closeable && (
          <button
            className="alert__dismiss"
            onClick={closeAlert}
            type="button"
            data-testid="alert-close-button"
          >
            <DismissIcon
              className={`alert__dismiss-icon alert__dismiss-icon--${type}`}
            />
          </button>
        )}
      </div>
    );
  }

  return null;
};

export default Alert;
