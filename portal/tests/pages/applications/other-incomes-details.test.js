import {
  MockClaimBuilder,
  renderWithAppLogic,
  testHook,
} from "../../test-utils";
import OtherIncome, { OtherIncomeType } from "../../../src/models/OtherIncome";
import OtherIncomesDetails, {
  OtherIncomeCard,
} from "../../../src/pages/applications/other-incomes-details";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import QuestionPage from "../../../src/components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../../src/components/RepeatableFieldset";
import RepeatableFieldsetCard from "../../../src/components/RepeatableFieldsetCard";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

describe("OtherIncomesDetails", () => {
  let appLogic, claim, wrapper;

  describe("when the user's claim has other income sources", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder().continuous().otherIncome().create();

      ({ appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
        claimAttrs: claim,
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
          }
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
          }
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
          }
        );
      });
    });
  });

  describe("when the user's claim does not have employer benefits", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder().continuous().create();

      ({ appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomesDetails, {
        claimAttrs: claim,
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
  let wrapper;
  const index = 0;

  beforeEach(() => {
    const entry = new OtherIncome();
    let getFunctionalInputProps;

    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: {},
        updateFields: jest.fn(),
      });
    });

    wrapper = shallow(
      <OtherIncomeCard
        entry={entry}
        index={index}
        getFunctionalInputProps={getFunctionalInputProps}
      />
    );
  });

  it("renders fields for an OtherIncome instance", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("doesn't include Unknown as a benefit type option", () => {
    const field = wrapper.find({
      name: `other_incomes[${index}].income_type`,
    });

    expect(field.prop("choices")).not.toContainEqual(
      expect.objectContaining({ value: OtherIncomeType.unknown })
    );
  });
});
