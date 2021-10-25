import { useEffect, useState } from "react";
import usePreviousValue from "../hooks/usePreviousValue";
import { zipObject } from "lodash";

interface ConditionalContentProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  children: any;
  /**
   * Field names, individually passed into `clearField` when the
   * content is hidden and this component unmounts. If you include
   * this prop, then remember to also pass in the `clearField` prop.
   */
  fieldNamesClearedWhenHidden?: string[];
  /**
   * Method called to remove a field's value from your app's state.
   */
  clearField?: (arg: string) => void;
  /**
   * Method called to cache the value of each field listed in `fieldNamesClearedWhenHidden`
   */
  getField?: (fieldName: string) => unknown;
  /**
   * Method called to restore the previous values of all fields listed in `fieldNamesClearedWhenHidden`
   */
  updateFields?: (arg: Record<string, unknown>) => void;
  visible?: boolean;
}

/**
 * Conditionally displays the content passed into it, and clears any
 * fields if they're hidden when the component unmounts. Based on
 * Vermont's Integrated Benefits `ConditionalContent` component.
 */
const ConditionalContent = (props: ConditionalContentProps) => {
  const {
    fieldNamesClearedWhenHidden,
    clearField,
    getField,
    updateFields,
    visible,
    children,
  } = props;
  const previouslyVisible = usePreviousValue(visible);
  const [hiddenFieldsValues, setHiddenFieldsValues] = useState({});

  useEffect(() => {
    if (!fieldNamesClearedWhenHidden) return;

    // Component changes from visible to hidden
    if (previouslyVisible && visible === false) {
      const dataToSave = zipObject(
        fieldNamesClearedWhenHidden,
        fieldNamesClearedWhenHidden.map(getField)
      );
      setHiddenFieldsValues(dataToSave);
      fieldNamesClearedWhenHidden.forEach((field) => clearField(field));
      // Creating an anon function because `forEach` passes in extra parameters (index, array) that clearField does not need
    }
    // Component changes from hidden to visible
    else if (previouslyVisible === false && visible) {
      updateFields(hiddenFieldsValues);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  if (!visible) return null;
  return children;
};

export default ConditionalContent;
