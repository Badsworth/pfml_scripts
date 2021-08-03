import React, { useRef, useState } from "react";

import Fieldset from "./Fieldset";
import FormLabel from "./FormLabel";
import PropTypes from "prop-types";
import classnames from "classnames";
import useUniqueId from "../hooks/useUniqueId";

/**
 * A combobox (`select` + `input`) allows users to search from a big set of options in a temporary modal menu and select one of them.
 * Also renders supporting UI elements like a `label`, hint text, and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/combo-box/)
 */
function ComboBox(props) {
  const hasError = !!props.errorMsg;
  const inputId = useUniqueId("ComboBox");
  const listRef = useRef(null);
  const inputRef = useRef(null);
  const boxRef = useRef(null);
  const isPristine = props.choices.find((c) => c.label === props.value)
    ? "usa-combo-box--pristine"
    : "";

  const [isMouseSelectingOption, setIsMouseSelectingOption] = useState(false);
  /* const fieldClasses = classnames(
    "usa-select usa-sr-only usa-combo-box__select maxw-mobile-lg",
    {
      "usa-input--error": hasError,
    }
  ); */

  const formGroupClasses = classnames(
    "usa-form-group",
    props.formGroupClassName,
    {
      "usa-form-group--error": hasError,
    }
  );

  const onClickToggleChoices = (e) => {
    if (listRef.current.getAttribute("hidden")) {
      listRef.current.removeAttribute("hidden");
    } else {
      hideOptionsList();
      e.target.blur();
    }
  };

  const hideOptionsList = () => {
    listRef.current.setAttribute("hidden", "hidden");
    inputRef.current.blur();
  };

  const onFocus = () => {
    listRef.current.removeAttribute("hidden");
  };

  const onBlur = () => {
    if (!inputRef.current || !listRef.current) return;
    if (!props.value && !isMouseSelectingOption) hideOptionsList();
  };

  const onChoiceFocus = (e) => {
    e.target.setAttribute("tabindex", "0");
    e.target.classList.add("usa-combo-box__list-option--focused");
    inputRef.current.setAttribute("aria-activedescendant", e.target.id);
  };

  const onChoiceBlur = (e) => {
    if (!e.target.classList.contains("usa-combo-box__list-option--selected")) {
      e.target.setAttribute("tabindex", "-1");
      e.target.classList.remove("usa-combo-box__list-option--focused");
    } else if (!isMouseSelectingOption) {
      hideOptionsList();
    }
  };
  const onChoiceMouseOver = onChoiceFocus;
  const onChoiceMouseOut = onChoiceBlur;

  const onKeyDown = (e) => {
    if (["ArrowUp", "ArrowDown"].includes(e.key)) {
      e.preventDefault();
      const listElement = document.querySelector(".usa-combo-box__list-option");
      listElement.focus();
      listElement.click();
    }
  };
  const onChoiceKeyDown = (e) => {
    e.preventDefault();
    let { target } = e;

    switch (e.key) {
      case "ArrowUp":
        target = target.previousSibling || inputRef.current;
        break;
      case "ArrowDown":
        target = target.nextSibling || inputRef.current;
        break;
      case "Enter":
        onBlur();
        return true;
    }

    target.focus();
    target.click();
  };

  const onChoiceChange = (e) => {
    const targetValue = e.target.getAttribute("data-value");
    const selectedOption = props.choices.find(
      (c) => c.value.toString() === targetValue
    );
    if (selectedOption) {
      // <li> tags don't have a value, so we simulate an input onchange event
      const onChangeEvent = new Event("onchange");
      inputRef.current.dispatchEvent(onChangeEvent);
      onChangeEvent.target.value = selectedOption.label;
      props.onChange(onChangeEvent);
    }
  };

  const onComboBoxMouseEnter = (e) => {
    setIsMouseSelectingOption(true);
  };
  const onComboBoxMouseLeave = (e) => {
    setIsMouseSelectingOption(false);
    hideOptionsList();
  };

  const clearSearch = (e) => {
    // change button event target as if it's an input element
    e.target.name = props.name;
    e.target.value = "";
    // trigger value change
    props.onChange(e);
    inputRef.current.focus();
  };

  const customBtnSpacing = {
    right: "calc(2.45em + 2px)",
  };

  let searchResults = props.choices.reduce((choices, choice, i) => {
    const isSelected = choice.label === props.value;
    if (
      choice.label
        .toLowerCase()
        .includes(props.value.toString().toLowerCase()) ||
      isPristine
    ) {
      // @todo: use classnames package
      const choiceClasses = ["usa-combo-box__list-option"];
      if (isSelected) {
        choiceClasses.push("usa-combo-box__list-option--selected");
        choiceClasses.push("usa-combo-box__list-option--focused");
      }
      choices.push(
        <li
          key={choice.value}
          id={props.name + "--list--option-" + i}
          className={choiceClasses.join(" ")}
          data-value={choice.value}
          aria-selected={isSelected}
          role="option"
          aria-setsize="64"
          aria-posinset="1"
          onMouseOver={onChoiceMouseOver}
          onMouseOut={onChoiceMouseOut}
          onFocus={onChoiceFocus}
          onBlur={onChoiceBlur}
          onClick={onChoiceChange}
          onKeyDown={onChoiceKeyDown}
          tabIndex={isSelected ? "0" : "-1"}
        >
          {choice.label}
        </li>
      );
    }
    return choices;
  }, []);

  if (!searchResults.length) {
    searchResults = (
      <li className="usa-combo-box__list-option--no-results">
        {props.emptyChoiceLabel || "No matches"}
      </li>
    );
  }

  return (
    <Fieldset className={formGroupClasses}>
      <FormLabel
        errorMsg={props.errorMsg}
        hint={props.hint}
        inputId={inputId}
        optionalText={props.optionalText}
        small={props.smallLabel}
        labelClassName={props.labelClassName}
      >
        {props.label}
      </FormLabel>
      <div
        ref={boxRef}
        className={["usa-combo-box", isPristine].join(" ")}
        onMouseEnter={onComboBoxMouseEnter}
        onMouseLeave={onComboBoxMouseLeave}
      >
        {/* "usa-select" class to use the "<select>" chevron */}
        <input
          id={props.name}
          name={props.name}
          type="text"
          className="usa-combo-box__input"
          ref={inputRef}
          role="combobox"
          aria-owns={props.name + "--list"}
          aria-autocomplete="list"
          aria-describedby={props.name + "--assistiveHint"}
          aria-expanded="false"
          aria-controls=""
          autoCapitalize="off"
          autoComplete="off"
          aria-activedescendant=""
          onBlur={onBlur}
          onFocus={onFocus}
          onChange={props.onChange}
          onKeyDown={onKeyDown}
          value={props.value}
        />
        <span className="usa-combo-box__clear-input__wrapper" tabIndex="-1">
          <button
            onClick={clearSearch}
            type="button"
            className="usa-combo-box__clear-input"
            aria-label="Clear the select contents"
            style={customBtnSpacing}
          >
            &nbsp;
          </button>
        </span>
        {isPristine && (
          <span
            className="usa-combo-box__input-button-separator"
            style={customBtnSpacing}
          >
            &nbsp;
          </span>
        )}
        <span className="usa-combo-box__toggle-list__wrapper" tabIndex="-1">
          <button
            type="button"
            tabIndex="-1"
            className="usa-combo-box__toggle-list"
            aria-label="Toggle the dropdown list"
            onClick={onClickToggleChoices}
            onBlur={hideOptionsList}
          >
            &nbsp;
          </button>
        </span>
        <ul
          ref={listRef}
          id={props.name + "--list"}
          className="usa-combo-box__list"
          aria-labelledby={inputId}
          role="listbox"
          tabIndex="-1"
          hidden
        >
          {searchResults}
        </ul>
      </div>
    </Fieldset>
  );
}

ComboBox.propTypes = {
  /**
   * List of choices to be rendered in the dropdown
   */
  choices: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.oneOfType([PropTypes.number, PropTypes.string])
        .isRequired,
      value: PropTypes.oneOfType([PropTypes.number, PropTypes.string])
        .isRequired,
    })
  ).isRequired,
  /**
   * Localized label for the initially selected option when no value is set
   */
  emptyChoiceLabel: PropTypes.string,
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized hint text
   */
  hint: PropTypes.node,
  /**
   * Override the label's default text-bold class
   */
  labelClassName: PropTypes.string,
  /**
   * Additional classes to include on the containing form group element
   */
  formGroupClassName: PropTypes.string,
  /**
   * Localized label
   */
  label: PropTypes.node.isRequired,
  /**
   * HTML input `name` attribute
   */
  name: PropTypes.string.isRequired,
  /**
   * Localized text indicating this field is optional
   */
  optionalText: PropTypes.node,
  /**
   * HTML input `onChange` attribute
   */
  onChange: PropTypes.func,
  /**
   * Enable the smaller label variant
   */
  smallLabel: PropTypes.bool,
  /** The `value` of the selected choice */
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
};

export default ComboBox;
