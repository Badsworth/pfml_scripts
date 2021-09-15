import AlertBar from "../../src/components/AlertBar";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "AlertBar body text",
    },
    customProps
  );

  const component = <AlertBar {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("AlertBar", () => {
  it("renders the children as the alert body text", () => {
    const { wrapper } = render({
      children: (
        <div>
          This is a test alert with <strong>bold text</strong>
        </div>
      ),
    });

    expect(wrapper.find(".margin-0.text-ink")).toMatchInlineSnapshot(`
      <p
        className="margin-0 text-ink"
      >
        <div>
          This is a test alert with 
          <strong>
            bold text
          </strong>
        </div>
      </p>
    `);
  });
});
