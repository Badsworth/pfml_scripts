import React, { useEffect, useRef, useState } from "react";
import Button from "./Button";
import PropTypes from "prop-types";
import RepeatableFieldsetCard from "./RepeatableFieldsetCard";
import classnames from "classnames";
import { uniqueId } from "lodash";
import usePreviousValue from "../hooks/usePreviousValue";

/**
 * Used for rendering the same set of content and fields for each
 * item in the "entries" prop.
 */
const RepeatableFieldset = (props) => {
  const { entries } = props;
  const containerRef = useRef<HTMLElement>();
  const entriesAndIds = useEntryIds(entries);
  const previousEntriesLength = usePreviousValue(entriesAndIds.length);
  const limitReached = props.limit ? entries.length >= props.limit : false;

  useEffect(() => {
    // @ts-expect-error ts-migrate(2532) FIXME: Object is possibly 'undefined'.
    if (entriesAndIds.length > previousEntriesLength) {
      // When a new entry is added to the list, focus and scroll it into view.
      const lastEntry = containerRef.current.querySelector(
        ".js-repeated-fieldset-card:last-of-type"
      );
      const focusableElement = lastEntry.querySelector(
        "[tabIndex]:first-child, label"
      );

      if (focusableElement instanceof HTMLElement) focusableElement.focus();
    }
  }, [containerRef, entriesAndIds.length, previousEntriesLength]);

  const limitMessageClasses = classnames(
    // full-width on small screens, beside button on larger screens
    "display-block",
    "mobile-lg:display-inline-block",
    // margin between button only on small screens
    "margin-top-1",
    "mobile-lg:margin-top-0",
    // center text to align with spinner on small screens
    "text-center",
    "mobile-lg:text-left"
  );

  return (
    <section className="margin-bottom-4" ref={containerRef}>
      {entriesAndIds.map(([entry, id], index) => (
        <RepeatableFieldsetCard
          key={id}
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
      <Button
        name="add-entry-button"
        onClick={props.onAddClick}
        variation="outline"
        disabled={limitReached}
      >
        {props.addButtonLabel}
      </Button>
      {limitReached && (
        <strong className={limitMessageClasses}>{props.limitMessage}</strong>
      )}
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
   * Maximum number of repeatable fields
   */
  limit: PropTypes.number,
  /**
   * Message to display when max number of repeatable fields have been added
   */
  limitMessage: PropTypes.string,
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

/**
 * Takes an array of entries, and pair each entry with a unique id.
 * The entry-id mapping remains stable across re-renders.
 * Returns an array of [entry, id] pairs.
 * @param {Array} entries List of entries
 * @returns {[*,string][]} List of entry, id pairs
 */
function useEntryIds(entries) {
  const [entryIdMap, setEntryIdMap] = useState(createEntryIdMap(entries));
  useEffect(() => {
    setEntryIdMap(createEntryIdMap(entries, entryIdMap));

    // No need to add entryIdMap to dependency list since entryIdMap
    // only depends on entries and entries is already in the dependency list.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entries]);
  return Array.from(entryIdMap.entries());
}

/**
 * Create a map from entries to ids.
 * If the entry already existed previously, use the same id.
 * Otherwise, create a new id.
 * @param {Array} entries List of entries
 * @param {Map<*,string>} [prevEntryIdMap] Previous map from entries to ids
 */
function createEntryIdMap(entries, prevEntryIdMap = new Map()) {
  const entryIdMap = new Map();
  for (const entry of entries) {
    const entryId = prevEntryIdMap.get(entry);
    if (entryId) {
      entryIdMap.set(entry, entryId);
    } else {
      entryIdMap.set(entry, uniqueId("RepeatableFieldset"));
    }
  }
  return entryIdMap;
}

export default RepeatableFieldset;
