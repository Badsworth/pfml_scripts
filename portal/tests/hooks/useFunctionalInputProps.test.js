import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { testHook } from "../test-utils";
import useFormState from "../../src/hooks/useFormState";
import useFunctionalInputProps from "../../src/hooks/useFunctionalInputProps";

describe("useFunctionalInputProps", () => {
  it("sets the value to a blank string when a field value is null", () => {
    let getFunctionalInputProps;
    testHook(() => {
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
    testHook(() => {
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

  it("gets the value from the formState by the field path", () => {
    let getFunctionalInputProps;
    testHook(() => {
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

    testHook(() => {
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

  it("sets the name and onChange props", () => {
    const name = "first_name";
    let getFunctionalInputProps;
    testHook(() => {
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
