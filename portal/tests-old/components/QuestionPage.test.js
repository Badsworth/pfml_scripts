import QuestionPage from "../../src/components/QuestionPage";
import React from "react";
import { shallow } from "enzyme";

describe("QuestionPage", () => {
  const sampleRoute = "/";
  const sampleTitle = "This is a question page";

  it("renders the form", () => {
    const wrapper = shallow(
      <QuestionPage
        title={sampleTitle}
        onSave={jest.fn(() => Promise.resolve())}
        nextPage={sampleRoute}
      >
        <div>Some stuff here</div>
      </QuestionPage>
    );
    expect(wrapper).toMatchSnapshot();
  });

  it("calls onSave with formData", async () => {
    const handleSave = jest.fn(() => Promise.resolve());
    const wrapper = shallow(
      <QuestionPage title={sampleTitle} onSave={handleSave}>
        <div>Some stuff here</div>
      </QuestionPage>
    );
    const event = { preventDefault: jest.fn() };

    await wrapper.find("form").simulate("submit", event);

    expect(handleSave).toHaveBeenCalled();
  });
});
