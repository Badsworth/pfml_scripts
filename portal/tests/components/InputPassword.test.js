import { mount, shallow } from "enzyme";
import InputChoice from "../../src/components/InputChoice";
import InputPassword from "../../src/components/InputPassword";
import InputText from "../../src/components/InputText";
import React from "react";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      label: "Field Label",
      name: "field-name",
      onChange: jest.fn(),
    },
    customProps
  );

  const component = <InputPassword {...props} />;

  return {
    props,
    wrapper: mountComponent ? mount(component) : shallow(component),
  };
}

describe("InputPassword", () => {
  it("defaults to a password input", () => {
    const { wrapper } = render();

    expect(wrapper.find(InputText).prop("type")).toBe("password");
  });

  describe("when checkbox is clicked", () => {
    it("toggles the input type", async () => {
      const { wrapper } = render();

      await wrapper.find(InputChoice).simulate("change", {
        preventDefault: jest.fn(),
      });

      expect(wrapper.find(InputText).prop("type")).toBe("text");
    });
  });

  it("generates a unique id", () => {
    const { wrapper: wrapper1 } = render({ name: "one" });
    const { wrapper: wrapper2 } = render({ name: "two" });

    const input1 = wrapper1.find(InputText);
    const input2 = wrapper2.find(InputText);

    const idRegex = /InputPassword[0-9]+/;

    expect(input1.prop("inputId")).toMatch(idRegex);
    expect(input1.prop("inputId")).not.toBe(input2.prop("inputId"));
  });
});
