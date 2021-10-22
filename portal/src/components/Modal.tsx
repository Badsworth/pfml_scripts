import Icon from "./Icon";
import React from "react";
import classnames from "classnames";

interface ModalProps {
  isVisible?: boolean;
  children: React.ReactNode;
  footer?: React.ReactNode;
  headingText?: string;
  onCloseButtonClick: () => void;
}

const Modal = (props: ModalProps) => {
  const { children, headingText, footer, isVisible, onCloseButtonClick } =
    props;

  return (
    <div
      className={classnames("usa-modal-wrapper", {
        "is-hidden": !isVisible,
        "is-visible": isVisible,
      })}
    >
      <div className="usa-modal-overlay">
        <div className="usa-modal" tabIndex={-1}>
          <div className="usa-modal__content">
            <div className="usa-modal__main">
              {headingText && (
                <h2 className="usa-modal__heading">{headingText}</h2>
              )}
              {children}
              {footer && <div className="usa-modal__footer">{footer}</div>}
            </div>
            <button
              className="usa-button usa-modal__close"
              type="button"
              onClick={onCloseButtonClick}
              aria-label="Close this window"
            >
              <Icon name="close" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Modal;
