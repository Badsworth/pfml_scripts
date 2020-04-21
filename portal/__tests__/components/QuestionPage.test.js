import QuestionPage from "../../src/components/QuestionPage";
import React from "react";
import { mockRouter } from "next/router";
import { shallow } from "enzyme";

describe("QuestionPage", () => {
  const sampleRoute = "/";
  const sampleTitle = "This is a question page";

  it("renders the form", () => {
    const wrapper = shallow(
      <QuestionPage
        title={sampleTitle}
        onSave={jest.fn()}
        nextPage={sampleRoute}
      >
        <div>Some stuff here</div>
      </QuestionPage>
    );
    expect(wrapper).toMatchSnapshot();
  });

  it("calls onSave with formData and redirects to address after submit", async () => {
    const handleSave = jest.fn();
    const formState = { a: 1, b: 2 };
    const wrapper = shallow(
      <QuestionPage
        title={sampleTitle}
        formState={formState}
        onSave={handleSave}
        nextPage={sampleRoute}
      >
        <div>Some stuff here</div>
      </QuestionPage>
    );
    const event = { preventDefault: jest.fn() };

    await wrapper.find("form").simulate("submit", event);

    expect(handleSave).toHaveBeenCalledWith(formState);
    expect(mockRouter.push).toHaveBeenCalledWith(sampleRoute);
  });
});
