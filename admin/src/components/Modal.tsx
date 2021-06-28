import { MouseEvent } from "react";

type Props = {
  title: string;
  body: string;
  handleCancelCallback: Function;
  handleContinueCallback: Function;
};

const Modal = ({
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
    <dialog open className="modal">
      <div className="modal__background"></div>
      <div className="modal__content">
        <h2 className="modal__title">{title}?</h2>
        <div className="modal__body">
          <p>{body}</p>
        </div>
        <div className="modal__action-buttons modal__action-buttons--stacked">
          <button className="btn" onClick={handleContinue}>
            <span className="btn__text">Continue</span>
          </button>
          <button className="btn" onClick={handleCancel}>
            <span className="btn__text">Cancel</span>
          </button>
        </div>
      </div>
    </dialog>
  );
};

export default Modal;
