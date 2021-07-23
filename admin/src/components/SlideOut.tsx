import Button from "../components/Button";
import { MouseEvent } from "react";

type Props = {
  title: string;
  isOpen?: boolean;
  onClose?: (event: MouseEvent) => void;
  children?: React.ReactNode;
};

const SlideOut = ({ title, isOpen, onClose, children }: Props) => {
  return (
    <dialog className="slide-out" open={isOpen}>
      <div className="slide-out__background" onClick={onClose}></div>
      <div className="slide-out__content">
        <div className="slide-out__header">
          <h2 className="slide-out__title">{title}</h2>
          <button
            className="slide-out__btn-close btn"
            onClick={onClose}
          ></button>
        </div>
        <div className="slide-out__body">{children}</div>
      </div>
    </dialog>
  );
};

export default SlideOut;
