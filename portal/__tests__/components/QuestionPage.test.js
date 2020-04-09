import * as nextRouter from "next/router";
import QuestionPage from "../../src/components/QuestionPage";
import React from "react";
import { shallow } from "enzyme";

describe("QuestionPage", () => {
  const sampleRoute = "/";
  const sampleTitle = "This is a question page";

  it("renders the form", () => {
    const wrapper = shallow(
      <QuestionPage title={sampleTitle} nextPage={sampleRoute}>
        <div>Some stuff here</div>
      </QuestionPage>
    );
    expect(wrapper).toMatchSnapshot();
  });

  it("redirects to address after submit", () => {
    const useRouter = jest.spyOn(nextRouter, "useRouter");
    const push = jest.fn();
    useRouter.mockImplementation(() => ({ push }));
    const wrapper = shallow(
      <QuestionPage title={sampleTitle} nextPage={sampleRoute}>
        <div>Some stuff here</div>
      </QuestionPage>
    );
    const event = { preventDefault: jest.fn() };

    wrapper.find("form").simulate("submit", event);

    expect(push).toHaveBeenCalledWith(sampleRoute);
  });
});
