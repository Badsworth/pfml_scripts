import * as React from "react";
import * as renderer from "react-test-renderer";
import ConfirmationDialog from "../../src/components/ConfirmationDialog";

it("ConfirmationDialog component renders correctly", () => {
  const modalCancelCallback = () => {};

  const modalContinueCallback = () => {};

  const props = {
    title: "test",
    body: "body",
    handleCancelCallback: modalCancelCallback,
    handleContinueCallback: modalContinueCallback,
  };
  const tree = renderer.create(<ConfirmationDialog {...props} />).toJSON();
  expect(tree).toMatchSnapshot();
});
