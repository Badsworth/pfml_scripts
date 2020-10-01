/**
 * @file test behavior and features common to all claims pages
 */
import LeaveReasonPage from "../../../src/pages/claims/leave-reason";
import NotifiedEmployer from "../../../src/pages/claims/notified-employer";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

const testPages = [LeaveReasonPage, NotifiedEmployer];

describe("Shared claims page behavior", () => {
  for (const Page of testPages) {
    describe(Page.name, () => {
      it("updates claim in API when user submits", () => {
        const { appLogic, wrapper } = renderWithAppLogic(Page);
        const event = { preventDefault: jest.fn() };
        wrapper.find("QuestionPage").simulate("save", event);

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          expect.any(String),
          expect.any(Object)
        );
      });
    });
  }
});
