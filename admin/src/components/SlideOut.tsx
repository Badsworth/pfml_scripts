import { CommonProps } from "../hooks/usePopup";

export type Props<T = unknown> = {
  title: string;
} & Partial<CommonProps<T>>;

const SlideOut = <T,>(props: Props<T>) => {
  const { isOpen, close, title, children, data } = props;
  return (
    <dialog className="slide-out" open={isOpen}>
      <div className="slide-out__background" onClick={close}></div>
      <div className="slide-out__content">
        <div className="slide-out__header">
          <h2 className="slide-out__title">{title}</h2>
          <button
            className="slide-out__btn-close"
            type="button"
            onClick={close}
            aria-label={`Close ${title} window`}
          ></button>
        </div>
        <div className="slide-out__body">
          {typeof children === "function" ? children(data) : children}
        </div>
      </div>
    </dialog>
  );
};

export default SlideOut;
