type Props = {
  title: string;
};

const Modal = ({ title }: Props) => {
  return (
    <div className="modal" tabIndex={0}>
      <div className="modal__background"></div>
      <div className="modal__content">
        <div className="modal__title">{title}?</div>
        <div className="modal__copy">
          Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
          eiusmod tempor incididunt ut labore et dolore magna aliqua.
        </div>
        <div className="modal__action-buttons modal__action-buttons--stacked">
          <button>Continue</button>
          <button>Cancel</button>
        </div>
      </div>
    </div>
  );
};

export default Modal;
