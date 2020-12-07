import {
  MockClaimBuilder,
  renderWithAppLogic,
  testHook,
} from "../../test-utils";
import PreviousLeave, {
  PreviousLeaveReason,
} from "../../../src/models/PreviousLeave";
import PreviousLeaveDetails, {
  PreviousLeaveCard,
} from "../../../src/pages/applications/previous-leaves-details";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import QuestionPage from "../../../src/components/QuestionPage";
import React from "react";
import RepeatableFieldset from "../../../src/components/RepeatableFieldset";
import RepeatableFieldsetCard from "../../../src/components/RepeatableFieldsetCard";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

describe("PreviousLeavesDetails", () => {
  let appLogic, claim, wrapper;

  describe("when the user's claim has previous leaves", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder()
        .employed()
        .continuous()
        .previousLeavePregnancyFromOtherEmployer()
        .create();

      ({ appLogic, wrapper } = renderWithAppLogic(PreviousLeaveDetails, {
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
            previous_leaves: claim.previous_leaves,
          }
        );
      });
    });

    describe("when user clicks 'Add another'", () => {
      it("adds another entry", () => {
        act(() => {
          wrapper.find(RepeatableFieldset).simulate("addClick");
          wrapper.find(QuestionPage).simulate("save");
        });

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            previous_leaves: [...claim.previous_leaves, new PreviousLeave()],
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
            previous_leaves: [],
          }
        );
      });
    });

    describe("when the user's claim does not have previous leaves", () => {
      beforeEach(() => {
        claim = new MockClaimBuilder().employed().continuous().create();

        ({ appLogic, wrapper } = renderWithAppLogic(PreviousLeaveDetails, {
          claimAttrs: claim,
        }));
      });

      it("adds a blank entry so a card is rendered", () => {
        const entries = wrapper.find("RepeatableFieldset").prop("entries");

        expect(entries).toHaveLength(1);
        expect(entries[0]).toEqual(new PreviousLeave());
      });
    });

    describe("PreviousLeaveCard", () => {
      let wrapper;
      const index = 0;

      beforeEach(() => {
        let getFunctionalInputProps;

        testHook(() => {
          getFunctionalInputProps = useFunctionalInputProps({
            appErrors: new AppErrorInfoCollection(),
            formState: {},
            updateFields: jest.fn(),
          });
        });

        wrapper = shallow(
          <PreviousLeaveCard
            employer_fein="12-3456789"
            entry={new PreviousLeave()}
            index={index}
            getFunctionalInputProps={getFunctionalInputProps}
          />
        );
      });

      it("renders fields for a PreviousLeave instance", () => {
        expect(wrapper).toMatchSnapshot();
      });

      it("doesn't include Unknown as a benefit type option", () => {
        const field = wrapper.find({
          name: `previous_leaves[${index}].leave_reason`,
        });

        expect(field.prop("choices")).not.toContainEqual(
          expect.objectContaining({ value: PreviousLeaveReason.unknown })
        );
      });
    });
  });
});
