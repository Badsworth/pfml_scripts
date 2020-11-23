import PreviousLeaveDetails, {
  PreviousLeaveCard,
} from "../../../src/pages/applications/previous-leaves-details";
import { renderWithAppLogic, testHook } from "../../test-utils";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import PreviousLeave from "../../../src/models/PreviousLeave";
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
      ({ appLogic, claim, wrapper } = renderWithAppLogic(PreviousLeaveDetails, {
        claimAttrs: { previous_leaves: [new PreviousLeave()] },
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
        ({ appLogic, claim, wrapper } = renderWithAppLogic(
          PreviousLeaveDetails,
          {
            claimAttrs: { previous_leaves: [new PreviousLeave()] },
          }
        ));
      });

      it("adds a blank entry so a card is rendered", () => {
        const entries = wrapper.find("RepeatableFieldset").prop("entries");

        expect(entries).toHaveLength(1);
        expect(entries[0]).toEqual(new PreviousLeave());
      });
    });

    describe("PreviousLeaveCard", () => {
      it("renders fields for a PreviousLeave instance", () => {
        let getFunctionalInputProps;

        testHook(() => {
          getFunctionalInputProps = useFunctionalInputProps({
            appErrors: new AppErrorInfoCollection(),
            formState: {},
            updateFields: jest.fn(),
          });
        });

        const wrapper = shallow(
          <PreviousLeaveCard
            index={0}
            getFunctionalInputProps={getFunctionalInputProps}
          />
        );

        expect(wrapper).toMatchSnapshot();
      });
    });
  });
});
