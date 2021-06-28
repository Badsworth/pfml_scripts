import * as React from "react";
import * as renderer from "react-test-renderer";
import Modal from "../../src/components/Modal";

it("SubjectToBeTested renders correctly", () => {
  const modalCancelCallback = () => {};

  const modalContinueCallback = () => {};

  const props = {
    title: "test",
    body: "body",
    handleCancelCallback: modalCancelCallback,
    handleContinueCallback: modalContinueCallback,
  };
  const tree = renderer.create(<Modal {...props} />).toJSON();
  expect(tree).toMatchSnapshot();
});
