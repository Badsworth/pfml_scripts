import OtherIncomesDetails, {
  OtherIncomeCard,
} from "../../../src/pages/claims/other-incomes-details";
import OtherIncome from "../../../src/models/OtherIncome";
import QuestionPage from "../../../src/components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../../src/components/RepeatableFieldset";
import RepeatableFieldsetCard from "../../../src/components/RepeatableFieldsetCard";
import { act } from "react-dom/test-utils";
import { renderWithAppLogic } from "../../test-utils";
import { shallow } from "enzyme";

jest.mock("../../../src/hooks/useAppLogic");

describe("OtherIncomesDetails", () => {
  let appLogic, claim, wrapper;

  describe("when the user's claim has other income sources", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
        claimAttrs: { other_incomes: [new OtherIncome()] },
      }));
    });

    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
    });

    describe("when user clicks continue", () => {
      it("calls claims.update", () => {
        act(() => {
          wrapper.find(QuestionPage).simulate("save");
        });

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            other_incomes: claim.other_incomes,
          },
          expect.any(Array)
        );
      });
    });

    describe("when the user clicks 'Add another'", () => {
      it("adds another entry", () => {
        act(() => {
          wrapper.find(RepeatableFieldset).simulate("addClick");
          wrapper.find(QuestionPage).simulate("save");
        });

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            other_incomes: [...claim.other_incomes, new OtherIncome()],
          },
          expect.any(Array)
        );
      });
    });

    describe("when the user clicks 'Remove'", () => {
      it("removes the entry", () => {
        act(() => {
          wrapper
            .find(RepeatableFieldset)
            .dive()
            .find(RepeatableFieldsetCard)
            .simulate("removeClick");
          wrapper.find(QuestionPage).simulate("save");
        });
        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            other_incomes: [],
          },
          expect.any(Array)
        );
      });
    });
  });

  describe("when the user's claim does not have employer benefits", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
        claimAttrs: { other_incomes: [new OtherIncome()] },
      }));
    });

    it("adds a blank entry so a card is rendered", () => {
      const entries = wrapper.find("RepeatableFieldset").prop("entries");

      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(new OtherIncome());
    });
  });
});

describe("OtherIncomeCard", () => {
  it("renders fields for an OtherIncome instance", () => {
    const entry = new OtherIncome();
    const wrapper = shallow(
      <OtherIncomeCard entry={entry} index={0} onInputChange={jest.fn()} />
    );

    expect(wrapper).toMatchSnapshot();
  });
});
