import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
  testHook,
} from "../../../test-utils";
import Confirmation from "../../../../src/pages/employers/applications/confirmation";
import { act } from "react-dom/test-utils";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Confirmation", () => {
  const claim = new MockEmployerClaimBuilder()
    .completed()
    .reviewable(true)
    .create();
  const query = { absence_id: "mock-absence-id" };
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    appLogic.employers.claim = claim;

    act(() => {
      ({ wrapper } = renderWithAppLogic(Confirmation, {
        employerClaimAttrs: claim,
        props: {
          appLogic,
          query,
        },
      }));
    });
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });
});
