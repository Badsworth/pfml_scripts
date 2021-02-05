import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import FieldsetAddress from "../../src/components/FieldsetAddress";
import React from "react";
import { createInputElement } from "../test-utils";
import { shallow } from "enzyme";

describe("FieldsetAddress", () => {
  let formState, props, wrapper;

  beforeEach(() => {
    formState = {
      address: {
        city: null,
        line_1: null,
        line_2: null,
        state: null,
        zip: null,
      },
    };

    props = {
      appErrors: new AppErrorInfoCollection(),
      label: "What is your address?",
      name: "address",
      onChange: jest.fn(),
      value: formState.address,
    };
  });

  it("renders the component with null values", () => {
    wrapper = shallow(<FieldsetAddress {...props} />);

    expect(wrapper).toMatchSnapshot();
  });

  it("renders the component with existing values", () => {
    props.value.city = "Washington";
    props.value.line_1 = "1600 Pennsylvania Avenue NW";
    props.value.line_2 = "Rose Garden";
    props.value.state = "DC";
    props.value.zip = "20500";
    wrapper = shallow(<FieldsetAddress {...props} />);

    expect(wrapper).toMatchSnapshot();
  });

  describe("when the zip is longer than 5 digits", () => {
    it("formats numeric values as a ZIP+4 string", () => {
      wrapper = shallow(<FieldsetAddress {...props} />);
      wrapper
        .find({ name: "address.zip" })
        .dive()
        .find("Mask")
        .dive()
        .find("input")
        .simulate("blur", {
          target: createInputElement({
            name: "zip",
            type: "text",
            value: "205001234",
          }),
        });

      expect(props.onChange.mock.calls[0][0].target.value).toBe("20500-1234");
    });

    it("leaves ZIP+4 strings as they are", () => {
      wrapper = shallow(<FieldsetAddress {...props} />);

      wrapper
        .find({ name: "address.zip" })
        .dive()
        .find("Mask")
        .dive()
        .find("input")
        .simulate("blur", {
          target: createInputElement({
            name: "zip",
            type: "text",
            value: "20500-1234",
          }),
        });

      expect(props.onChange.mock.calls[0][0].target.value).toBe("20500-1234");
    });
  });

  describe("when there are errors", () => {
    it("display errors on the associated inputs", () => {
      props.appErrors = new AppErrorInfoCollection([
        new AppErrorInfo({
          field: "address.line_1",
          message: "Address is required",
        }),
        new AppErrorInfo({
          field: "address.line_2",
          message: "Address 2 is required",
        }),
        new AppErrorInfo({
          field: "address.city",
          message: "City is required",
        }),
        new AppErrorInfo({
          field: "address.state",
          message: "State is required",
        }),
        new AppErrorInfo({
          field: "address.zip",
          message: "ZIP is required",
        }),
      ]);
      wrapper = shallow(<FieldsetAddress {...props} />);

      const renderErrorMsg = (name) => {
        const Component = () => (
          <React.Fragment>
            {wrapper.find({ name }).prop("errorMsg")}
          </React.Fragment>
        );
        return shallow(<Component />).html();
      };

      expect(renderErrorMsg("address.line_1")).toEqual("Address is required");
      expect(renderErrorMsg("address.line_2")).toBe("Address 2 is required");
      expect(renderErrorMsg("address.city")).toBe("City is required");
      expect(renderErrorMsg("address.state")).toBe("State is required");
      expect(renderErrorMsg("address.zip")).toBe("ZIP is required");
    });
  });

  describe("when the smallLabel prop is set", () => {
    it("renders with a small label", () => {
      props.smallLabel = true;
      wrapper = shallow(<FieldsetAddress {...props} />);

      expect(wrapper.find("FormLabel").prop("small")).toBe(true);
    });
  });

  describe("when the hint prop is set", () => {
    it("renders the hint text", () => {
      props.hint = "This is a hint";
      wrapper = shallow(<FieldsetAddress {...props} />);

      expect(wrapper.find("FormLabel").prop("hint")).toBe(props.hint);
    });
  });

  describe("when the addressType prop is mailing", () => {
    it("renders alterative mailing address labels", () => {
      props.addressType = "mailing";
      wrapper = shallow(<FieldsetAddress {...props} />);

      const labelText = wrapper.find({ name: "address.line_1" }).prop("label");

      expect(labelText).toMatchInlineSnapshot(`"Mailing address"`);
    });
  });
});
