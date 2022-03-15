import Button from "./core/Button";
import React from "react";
import ThrottledButton from "./ThrottledButton";
import classnames from "classnames";

interface AmendmentFormProps {
  className?: string;
  onSave?: () => Promise<void>;
  saveButtonText?: string;
  onDestroy: React.MouseEventHandler<HTMLButtonElement>;
  children: React.ReactNode;
  destroyButtonLabel: string;
}

/**
 * Expandable form for amending an answer inline on a page.
 */
export const AmendmentForm = ({
  className = "",
  onSave,
  saveButtonText,
  onDestroy,
  children,
  destroyButtonLabel,
}: AmendmentFormProps) => {
  const classes = classnames(
    `usa-alert usa-alert--info usa-alert--no-icon usa-form c-amendment-form border-y border-y-width-1px border-right border-right-width-1px`,
    className
  );

  return (
    <div className={classes}>
      <div className="usa-alert__body">
        <div className="usa-alert__text">{children}</div>
        <div className="border-top border-width-1px margin-top-4 margin-bottom-1 border-base-light">
          {onSave && (
            <ThrottledButton onClick={onSave} className="margin-right-2">
              {saveButtonText}
            </ThrottledButton>
          )}
          <Button
            data-test="amendment-destroy-button"
            variation="unstyled"
            className="margin-top-3 text-red"
            onClick={onDestroy}
          >
            {destroyButtonLabel}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default AmendmentForm;
