import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
  testHook,
} from "../../test-utils";
import PreviousLeave, {
  PreviousLeaveReason,
} from "../../../src/models/PreviousLeave";
import PreviousLeaveDetails, {
  PreviousLeaveCard,
} from "../../../src/pages/applications/previous-leaves-details";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import React from "react";
import RepeatableFieldset from "../../../src/components/RepeatableFieldset";
import RepeatableFieldsetCard from "../../../src/components/RepeatableFieldsetCard";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

describe("PreviousLeavesDetails", () => {
  let appLogic, claim, submitForm, wrapper;

  describe("when the user's claim has previous leaves", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder()
        .employed()
        .continuous()
        .previousLeave([
          {
            is_for_current_employer: false,
            leave_end_date: "2020-02-01",
            leave_reason: PreviousLeaveReason.pregnancy,
            leave_start_date: "2020-01-01",
          },
          {
            is_for_current_employer: true,
            leave_end_date: "2020-02-05",
            leave_reason: PreviousLeaveReason.medical,
            leave_start_date: "2020-01-05",
          },
        ])
        .create();

      ({ appLogic, wrapper } = renderWithAppLogic(PreviousLeaveDetails, {
        claimAttrs: claim,
      }));
      submitForm = simulateEvents(wrapper).submitForm;
    });

    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
    });

    describe("when user clicks continue", () => {
      it("calls claims.update", async () => {
        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            previous_leaves: claim.previous_leaves,
          }
        );
      });
    });

    describe("when user clicks 'Add another'", () => {
      it("adds another entry", async () => {
        act(() => {
          wrapper.find(RepeatableFieldset).simulate("addClick");
        });
        await submitForm();

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            previous_leaves: [...claim.previous_leaves, new PreviousLeave()],
          }
        );
      });
    });

    describe("when the user clicks 'Remove'", () => {
      let removeButton;

      beforeEach(() => {
        removeButton = wrapper
          .find(RepeatableFieldset)
          .dive()
          .find(RepeatableFieldsetCard)
          .first()
          .dive()
          .find("Button");
      });

      describe("and the leave isn't saved to the API", () => {
        it("removes the leave", async () => {
          appLogic.claims.update.mockImplementationOnce(
            (applicationId, patchData) => {
              expect(applicationId).toBe(claim.application_id);
              expect(patchData.previous_leaves).toHaveLength(1);
            }
          );

          await act(async () => {
            await removeButton.simulate("click");
          });
          await submitForm();

          expect(
            appLogic.otherLeaves.removePreviousLeave
          ).not.toHaveBeenCalled();
          expect(appLogic.claims.update).toHaveBeenCalledTimes(1);
        });
      });

      describe("and the leave is saved to the API", () => {
        beforeEach(() => {
          claim.previous_leaves[0].previous_leave_id =
            "mock-employer-leave-id-1";
        });

        describe("when the DELETE request succeeds", () => {
          it("removes the leave", async () => {
            appLogic.claims.update.mockImplementationOnce(
              (applicationId, patchData) => {
                expect(applicationId).toBe(claim.application_id);
                expect(patchData.previous_leaves).toHaveLength(1);
              }
            );

            await act(async () => {
              await removeButton.simulate("click");
            });
            await submitForm();

            expect(appLogic.otherLeaves.removePreviousLeave).toHaveBeenCalled();
            expect(appLogic.claims.update).toHaveBeenCalledTimes(1);
          });
        });

        describe("when the DELETE request fails", () => {
          beforeEach(() => {
            appLogic.otherLeaves.removePreviousLeave.mockImplementationOnce(
              () => false
            );
          });

          it("does not remove the leave", async () => {
            appLogic.claims.update.mockImplementationOnce(
              (applicationId, patchData) => {
                expect(applicationId).toBe(claim.application_id);
                expect(patchData.previous_leaves).toHaveLength(2);
              }
            );

            await act(async () => {
              await removeButton.simulate("click");
            });
            await submitForm();

            expect(appLogic.otherLeaves.removePreviousLeave).toHaveBeenCalled();
            expect(appLogic.claims.update).toHaveBeenCalledTimes(1);
          });
        });
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
        const entries = wrapper.find(RepeatableFieldset).prop("entries");

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
