import { MouseEvent } from "react";
import Button from "./Button";

type Props = {
  title: string;
  body: string;
  handleCancelCallback: Function;
  handleContinueCallback: Function;
};

const ConfirmationDialog = ({
  title,
  body,
  handleCancelCallback,
  handleContinueCallback,
}: Props) => {
  const handleCancel = (event: MouseEvent) => {
    event.preventDefault();
    handleCancelCallback(event);
  };

  const handleContinue = (event: MouseEvent) => {
    event.preventDefault();
    handleContinueCallback(event);
  };

  return (
    <dialog open className="confirmation-dialog">
      <div className="confirmation-dialog__background"></div>
      <div className="confirmation-dialog__content">
        <h2 className="confirmation-dialog__title">{title}?</h2>
        <div className="confirmation-dialog__body">
          <p>{body}</p>
        </div>
        <div className="confirmation-dialog__action-buttons confirmation-dialog__action-buttons--stacked">
          <Button callback={handleContinue}>Continue</Button>
          <Button additionalClasses={["btn-cancel"]} callback={handleCancel}>
            Cancel
          </Button>
        </div>
      </div>
    </dialog>
  );
};

export default ConfirmationDialog;
