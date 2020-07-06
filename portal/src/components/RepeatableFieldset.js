import React, { useEffect, useState } from "react";
import Button from "./Button";
import PropTypes from "prop-types";
import RepeatableFieldsetCard from "./RepeatableFieldsetCard";
import usePreviousValue from "../hooks/usePreviousValue";

/**
 * Used for rendering the same set of content and fields for each
 * item in the "entries" prop.
 */
const RepeatableFieldset = (props) => {
  const { entries } = props;
  const previousEntriesLength = usePreviousValue(entries.length);
  const containerRef = React.createRef();
  // See setKeyIncrement usage below for context
  const [keyIncrement, setKeyIncrement] = useState(0);

  useEffect(() => {
    if (entries.length > previousEntriesLength) {
      // When a new entry is added to the list, focus and scroll it into view.
      const lastEntry = containerRef.current.querySelector(
        ".js-repeated-fieldset-card:last-of-type"
      );
      const focusableElement = lastEntry.querySelector(
        "[tabIndex]:first-child, label"
      );

      if (focusableElement) focusableElement.focus();
    } else if (entries.length < previousEntriesLength) {
      // When an entry is removed from the list, change keyIncrement so React
      // identifies that the existing RepeatableFieldsetCards no longer correspond
      // to their previous index position. This is avoids unexpected behavior
      // and fixes issues where the Remove button would remain focused, potentially
      // causing a confusing experience for screen readers.
      setKeyIncrement(keyIncrement + 1);
    }
  }, [containerRef, entries.length, keyIncrement, previousEntriesLength]);

  return (
    <section className="margin-bottom--3" ref={containerRef}>
      {entries.map((entry, index) => (
        <RepeatableFieldsetCard
          key={`${index}_${keyIncrement}`}
          className="js-repeated-fieldset-card"
          entry={entry}
          heading={`${props.headingPrefix} ${index + 1}`}
          index={index}
          removeButtonLabel={props.removeButtonLabel}
          onRemoveClick={props.onRemoveClick}
          showRemoveButton={entries.length > 1}
        >
          {props.render(entry, index)}
        </RepeatableFieldsetCard>
      ))}

      <Button onClick={props.onAddClick} variation="outline">
        {props.addButtonLabel}
      </Button>
    </section>
  );
};

RepeatableFieldset.propTypes = {
  /**
   * Localized text used in the "Add" button
   */
  addButtonLabel: PropTypes.string.isRequired,
  /** Array of entries, each of which will have the content repeated for. */
  entries: PropTypes.arrayOf(PropTypes.object).isRequired,
  /**
   * Displayed as the heading for each card, followed by the card's position. For example
   * if you specify "Person", headings will be "Person 1", "Person 2", etc.
   */
  headingPrefix: PropTypes.string.isRequired,
  /**
   * Function used for rendering the fields
   * @param {object} entry
   * @param {number} index
   * @returns {React.ReactNode}
   * @see https://reactjs.org/docs/render-props.html
   */
  render: PropTypes.func.isRequired,
  /**
   * Localized text used in the "Remove" buttons.
   * A "Remove" button isn't rendered when the
   * entries length is 1.
   */
  removeButtonLabel: PropTypes.string.isRequired,
  /**
   * Event handler responsible for adding a new entry
   */
  onAddClick: PropTypes.func.isRequired,
  /**
   * Event handler responsible for removing an entry
   * @param {object} entry
   * @param {number} index
   */
  onRemoveClick: PropTypes.func.isRequired,
};

export default RepeatableFieldset;
