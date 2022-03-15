import { ValidationError } from "../../src/errors";
import { render } from "@testing-library/react";
import { renderHook } from "@testing-library/react-hooks";
import useFormState from "../../src/hooks/useFormState";
import useFunctionalInputProps from "../../src/hooks/useFunctionalInputProps";

describe("useFunctionalInputProps", () => {
  it("sets the value to a blank string when a field value is null", () => {
    let getFunctionalInputProps;
    renderHook(() => {
      const { formState, updateFields } = useFormState({
        first_name: null,
      });

      getFunctionalInputProps = useFunctionalInputProps({
        errors: [],
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps("first_name");

    expect(props.value).toBe("");
  });

  it("sets the value to a blank string when a field value is undefined", () => {
    let getFunctionalInputProps;
    renderHook(() => {
      const { formState, updateFields } = useFormState({});

      getFunctionalInputProps = useFunctionalInputProps({
        errors: [],
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps("first_name");

    expect(props.value).toBe("");
  });

  it("sets the value to the given fallback value when a field value is null", () => {
    let getFunctionalInputProps;
    renderHook(() => {
      const { formState, updateFields } = useFormState({});

      getFunctionalInputProps = useFunctionalInputProps({
        errors: [],
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps("first_name", {
      fallbackValue: "default",
    });

    expect(props.value).toBe("default");
  });

  it("sets the value to 0 when the value is 0", () => {
    let getFunctionalInputProps;
    renderHook(() => {
      const { formState, updateFields } = useFormState({ minutes: 0 });

      getFunctionalInputProps = useFunctionalInputProps({
        errors: [],
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps("minutes");

    expect(props.value).toBe(0);
  });

  it("gets the value from the formState by the field path", () => {
    let getFunctionalInputProps;
    renderHook(() => {
      const { formState, updateFields } = useFormState({
        leave_details: { employer_notified: true },
      });

      getFunctionalInputProps = useFunctionalInputProps({
        errors: [],
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps("leave_details.employer_notified");

    expect(props.value).toBe(true);
  });

  it("sets the errorMsg prop to an error's message when one exists for the field", () => {
    let getFunctionalInputProps;
    const error = new ValidationError(
      [
        {
          field: "first_name",
        },
      ],
      "applications"
    );

    renderHook(() => {
      const { formState, updateFields } = useFormState({});

      getFunctionalInputProps = useFunctionalInputProps({
        errors: [error],
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps("first_name");
    const { container } = render(props.errorMsg);

    expect(container.firstChild).toMatchInlineSnapshot(
      `Field (first_name) has invalid value.`
    );
  });

  it("doesn't require errors to be defined", () => {
    let getFunctionalInputProps;

    renderHook(() => {
      const { formState, updateFields } = useFormState({
        employer_notified: true,
      });

      getFunctionalInputProps = useFunctionalInputProps({
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps("employer_notified");
    const { container } = render(props.errorMsg);

    expect(container).toBeEmptyDOMElement();
  });

  it("sets the name and onChange props", () => {
    const name = "first_name";
    let getFunctionalInputProps;
    renderHook(() => {
      const { formState, updateFields } = useFormState({
        first_name: null,
      });

      getFunctionalInputProps = useFunctionalInputProps({
        errors: [],
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps(name);

    expect(props.name).toBe(name);
    expect(props.onChange).toBeDefined();
  });
});
