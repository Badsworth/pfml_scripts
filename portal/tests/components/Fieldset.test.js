import Fieldset from "../../src/components/Fieldset";
import React from "react";
import { render } from "@testing-library/react";

const renderComponent = (customProps) => {
  return render(<Fieldset {...customProps} />);
};

describe("Fieldset", () => {
  it("renders Fieldset component with children", () => {
    const { container } = renderComponent({ children: "child" });

    expect(container).toMatchSnapshot();
  });

  it("appends classname to fieldset classnames when className prop is set", () => {
    const { container } = renderComponent({ className: "a-class" });

    expect(container.querySelector(".a-class").className).toEqual(
      "usa-fieldset a-class"
    );
  });
});
