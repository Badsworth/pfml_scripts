import React, { useState } from "react";

type Props = {
  type: "warn" | "success" | "info" | "error" | "neutral";
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

  if (showAlert) {
    return (
      <div className={`alert alert--${type}`}>
        <div className="alert__icon"></div>
        <div className="alert__text">{children}</div>
        {closeable && (
          <button
            className="alert__dismiss"
            onClick={closeAlert}
            type="button"
          ></button>
        )}
      </div>
    );
  }

  return null;
};

export default Alert;
