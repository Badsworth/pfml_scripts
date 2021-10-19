import Button from "./Button";
import React from "react";
import useUniqueId from "../hooks/useUniqueId";

interface RepeatableFieldsetCardProps {
  children: React.ReactNode;
  className?: string;
  entry: any;
  heading: string;
  index?: number;
  removeButtonLabel: string;
  onRemoveClick: (entry: Record<string, unknown>, index: number) => void;
  showRemoveButton?: boolean;
}

/**
 * Used by the `RepeatableFieldset` component. This is rendered
 * for each entry, and is responsible for rendering the
 * fieldset content.
 */
const RepeatableFieldsetCard = (props: RepeatableFieldsetCardProps) => {
  const id = useUniqueId("RepeatableFieldsetCard");

  const handleRemoveClick = async () => {
    await props.onRemoveClick(props.entry, props.index);
  };

  return (
    <div
      key={id}
      data-key={id}
      data-testid="repeatable-fieldset-card"
      className={`margin-bottom-3 measure-5 padding-3 border-2px border-base-lighter ${props.className}`}
    >
      <fieldset className="usa-fieldset">
        <legend className="usa-legend font-heading-lg text-normal">
          {props.heading}
        </legend>

        {props.children}

        {props.showRemoveButton && (
          <div className="border-top border-base-lighter padding-top-2 margin-top-2">
            <Button
              name="remove-entry-button"
              className="text-error hover:text-error-dark active:text-error-darker"
              onClick={handleRemoveClick}
              variation="unstyled"
            >
              {props.removeButtonLabel}
            </Button>
          </div>
        )}
      </fieldset>
    </div>
  );
};

export default RepeatableFieldsetCard;
