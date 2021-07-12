import { MouseEvent } from "react";
import Button from "./Button";

type Props = {
  title: string;
  handleCloseCallback: Function;
  children: React.ReactNode;
};

const SlideOut = ({ title, handleCloseCallback, children }: Props) => {
  const handleClose = (event: MouseEvent) => {
    event.preventDefault();
    handleCloseCallback(event);
  };

  return (
    <dialog open className="slide-out">
      <div className="slide-out__background"></div>
      <div className="slide-out__content">
        <div className="slide-out__header">
          <h2 className="slide-out__title">{title}</h2>
          <button className="slide-out__btn-close" onClick={handleClose}>
            x
          </button>
        </div>
        <div className="slide-out__body">{children}</div>
      </div>
    </dialog>
  );
};

export default SlideOut;
