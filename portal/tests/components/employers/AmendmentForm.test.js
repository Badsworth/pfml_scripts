import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import React from "react";
import { shallow } from "enzyme";

describe("AmendmentForm", () => {
  const onDestroy = jest.fn();
  const destroyButtonLabel = "Destroy";

  it("renders the component", () => {
    const wrapper = shallow(
      <AmendmentForm
        onDestroy={onDestroy}
        destroyButtonLabel={destroyButtonLabel}
      >
        <p>Testing</p>
      </AmendmentForm>
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("shows a button labeled with destroyButtonLabel", () => {
    const wrapper = shallow(
      <AmendmentForm
        onDestroy={onDestroy}
        destroyButtonLabel={destroyButtonLabel}
      >
        <p>Testing</p>
      </AmendmentForm>
    );

    expect(wrapper.find("Button").dive().text()).toEqual("Destroy");
  });

  it("calls 'onDestroy' when the destroy button is clicked", () => {
    const wrapper = shallow(
      <AmendmentForm
        onDestroy={onDestroy}
        destroyButtonLabel={destroyButtonLabel}
      >
        <p>Testing</p>
      </AmendmentForm>
    );
    wrapper.find("Button").simulate("click");

    expect(onDestroy).toHaveBeenCalled();
  });
});
