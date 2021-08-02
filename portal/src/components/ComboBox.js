import React, { useRef } from "react";

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
  const isPristine = props.choices.find((c) => c.value === props.value)
    ? "usa-combo-box--pristine"
    : "";

  const fieldClasses = classnames(
    "usa-select usa-sr-only usa-combo-box__select maxw-mobile-lg",
    {
      "usa-input--error": hasError,
    }
  );

  const formGroupClasses = classnames(
    "usa-form-group",
    props.formGroupClassName,
    {
      "usa-form-group--error": hasError,
    }
  );

  const onSearch = (e) => {
    props.updateField(e.target.value);
    searchResults = search();
  };
  const onMouseLeave = (e) => {
    listRef.current.setAttribute("hidden", "hidden");
    inputRef.current.blur();
  };
  // const onToggleChoices = (e) => {
  //   if (listRef.current.getAttribute("hidden")) {
  //     listRef.current.removeAttribute("hidden");
  //   } else {
  //     listRef.current.setAttribute("hidden", "hidden");
  //   }
  // };
  const onFocus = (e) => {
    listRef.current.removeAttribute("hidden");
  };
  const clearSearch = (e) => {
    props.updateField("");
    inputRef.current.focus();
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
    }
  };
  const onChoiceMouseOver = onChoiceFocus;
  const onChoiceMouseOut = onChoiceBlur;
  // eslint-disable-next-line no-console
  const onChoiceKeyDown = (e) => console.log(e.key);
  const onChoiceChange = (e) => {
    props.updateField(e.target.getAttribute("data-value"));
    listRef.current.setAttribute("hidden", "hidden");
    inputRef.current.blur();
  };

  const search = () => {
    const finalChoices = props.choices.reduce((choices, choice, i) => {
      const isSelected = choice.value === props.value;
      if (
        choice.value.toLowerCase().includes(props.value.toLowerCase()) ||
        choice.label.toLowerCase().includes(props.value.toLowerCase()) ||
        isPristine
      ) {
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
    if (finalChoices.length) {
      return finalChoices;
    } else {
      return (
        <li className="usa-combo-box__list-option--no-results">
          {props.emptyChoiceLabel}
        </li>
      );
    }
  };

  let searchResults = search();
  const customBtnSpacing = {
    right: "calc(2.1em + 2px)",
  };
  return (
    <div
      className={formGroupClasses}
      onMouseLeave={props.onMouseLeave ? props.onMouseLeave : onMouseLeave}
    >
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
        data-enhanced="true"
      >
        <select
          className={fieldClasses}
          name={props.name}
          onChange={props.onChange}
          value={props.value}
          tabIndex="-1"
        >
          {props.choices.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
        <input
          id={props.name}
          type="text"
          className="usa-select usa-combo-box__input"
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
          onFocus={props.onFocus ? props.onFocus : onFocus}
          onChange={onSearch}
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
        <span
          className="usa-combo-box__input-button-separator"
          style={customBtnSpacing}
        >
          &nbsp;
        </span>
        {/* Optional different chevron for the "select" field
        <span className="usa-combo-box__toggle-list__wrapper" tabIndex="-1">
          <button
            type="button"
            tabIndex="-1"
            className="usa-combo-box__toggle-list"
            aria-label="Toggle the dropdown list"
            onClick={onToggleChoices}
          >
            &nbsp;
          </button>
        </span> */}
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
    </div>
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
  emptyChoiceLabel: PropTypes.string.isRequired,
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
   * HTML input `onMouseLeave` attribute
   */
  onMouseLeave: PropTypes.func,
  /**
   * HTML input `onFocus` attribute
   */
  onFocus: PropTypes.func,
  /**
   * Enable the smaller label variant
   */
  smallLabel: PropTypes.bool,
  /** The `value` of the selected choice */
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),

  updateField: PropTypes.func,
};

export default ComboBox;
