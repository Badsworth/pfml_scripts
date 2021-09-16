import { act, render, screen } from "@testing-library/react";
import QuestionPage from "../../src/components/QuestionPage";
import React from "react";
import tracker from "../../src/services/tracker";
import userEvent from "@testing-library/user-event";

jest.mock("../../src/services/tracker");

describe("QuestionPage", () => {
  const sampleRoute = "/";
  const sampleTitle = "This is a question page";

  it("renders the form", () => {
    const { container } = render(
      <QuestionPage
        title={sampleTitle}
        onSave={jest.fn(() => Promise.resolve())}
        nextPage={sampleRoute}
      >
        <div>Some stuff here</div>
      </QuestionPage>
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it("calls onSave with formData", async () => {
    const handleSaveMock = jest.fn(() => Promise.resolve());
    render(
      <QuestionPage title={sampleTitle} onSave={handleSaveMock}>
        <div>Some stuff here</div>
      </QuestionPage>
    );
    await act(async () => {
      await userEvent.click(screen.getByRole("button"));
    });

    expect(handleSaveMock).toHaveBeenCalled();
    expect(tracker.trackEvent).not.toHaveBeenCalled();
  });

  it("tracks the event when onSave is not a Promise", async () => {
    jest.spyOn(console, "warn").mockImplementationOnce(jest.fn());
    const handleSaveMock = jest.fn();
    render(
      <QuestionPage title={sampleTitle} onSave={handleSaveMock}>
        <div>Some stuff here</div>
      </QuestionPage>
    );

    await act(async () => {
      await userEvent.click(screen.getByRole("button"));
    });

    expect(handleSaveMock).toHaveBeenCalled();
    expect(tracker.trackEvent).toHaveBeenCalled();
    expect(console.warn).toHaveBeenCalled(); // eslint-disable-line no-console
  });
});
