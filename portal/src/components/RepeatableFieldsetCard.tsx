import Button from "./Button";
import PropTypes from "prop-types";
import React from "react";
import useUniqueId from "../hooks/useUniqueId";

/**
 * Used by the `RepeatableFieldset` component. This is rendered
 * for each entry, and is responsible for rendering the
 * fieldset content.
 */
const RepeatableFieldsetCard = (props) => {
  const id = useUniqueId("RepeatableFieldsetCard");

  const handleRemoveClick = async () => {
    await props.onRemoveClick(props.entry, props.index);
  };

  return (
    <div
      key={id}
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

RepeatableFieldsetCard.propTypes = {
  /** Card content */
  children: PropTypes.node.isRequired,
  /** Additional classNames to add */
  className: PropTypes.string,
  /** The item this card is associated with */
  entry: PropTypes.object.isRequired,
  heading: PropTypes.string.isRequired,
  /** Index of this entry in the list of entries */
  index: PropTypes.number,
  /**
   * Localized text used in the "Remove" buttons.
   * A "Remove" button isn't rendered when the
   * entries length is 1.
   */
  removeButtonLabel: PropTypes.string.isRequired,
  /**
   * Event handler responsible for removing an entry
   * @param {object} entry
   * @param {number} index
   */
  onRemoveClick: PropTypes.func.isRequired,
  /**
   * Render the remove button so the user can remove the card
   */
  showRemoveButton: PropTypes.bool,
};

export default RepeatableFieldsetCard;
