import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
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
        appErrors: new AppErrorInfoCollection(),
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
        appErrors: new AppErrorInfoCollection(),
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
        appErrors: new AppErrorInfoCollection(),
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
        appErrors: new AppErrorInfoCollection(),
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
        appErrors: new AppErrorInfoCollection(),
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps("leave_details.employer_notified");

    expect(props.value).toBe(true);
  });

  it("sets the errorMsg prop to an error's message when one exists for the field", () => {
    let getFunctionalInputProps;
    const issue = new AppErrorInfo({
      message: "Field was invalid",
      field: "first_name",
    });

    renderHook(() => {
      const { formState, updateFields } = useFormState({
        leave_details: { employer_notified: true },
      });

      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection([issue]),
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps("leave_details.employer_notified");

    expect(props.errorMsg).toBe(issue.msg);
  });

  it("doesn't require appErrors to be defined", () => {
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

    expect(props.errorMsg).toBeUndefined();
  });

  it("sets the name and onChange props", () => {
    const name = "first_name";
    let getFunctionalInputProps;
    renderHook(() => {
      const { formState, updateFields } = useFormState({
        first_name: null,
      });

      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState,
        updateFields,
      });
    });

    const props = getFunctionalInputProps(name);

    expect(props.name).toBe(name);
    expect(props.onChange).toBeDefined();
  });
});
