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
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

const previousLeaves = [
  {
    is_for_current_employer: false,
    leave_end_date: "2020-02-01",
    leave_reason: PreviousLeaveReason.pregnancy,
    leave_start_date: "2020-01-01",
    previous_leave_id: null,
  },
  {
    is_for_current_employer: true,
    leave_end_date: "2020-02-05",
    leave_reason: PreviousLeaveReason.medical,
    leave_start_date: "2020-01-05",
    previous_leave_id: null,
  },
];

const setup = (options = { hasPreviousLeave: false }) => {
  let claim = new MockClaimBuilder().employed().continuous();

  if (options.hasPreviousLeave) {
    claim.previousLeave(previousLeaves);
  }

  claim = claim.create();

  const { appLogic, wrapper } = renderWithAppLogic(PreviousLeaveDetails, {
    claimAttrs: claim,
  });

  const { submitForm } = simulateEvents(wrapper);

  const clickAddPreviousLeave = () => {
    wrapper
      .find(RepeatableFieldset)
      .dive()
      .find({ name: "add-entry-button" })
      .simulate("click");
  };

  const clickRemoveFirstPreviousLeave = () => {
    wrapper
      .find(RepeatableFieldset)
      .dive()
      .find(RepeatableFieldsetCard)
      .first()
      .dive()
      .find({ name: "remove-entry-button" })
      .simulate("click");
  };

  return {
    appLogic,
    claim,
    clickAddPreviousLeave,
    clickRemoveFirstPreviousLeave,
    submitForm,
    wrapper,
  };
};

describe("PreviousLeavesDetails", () => {
  describe("when the user's claim has previous leaves", () => {
    it("renders the page", () => {
      const { wrapper } = setup({ hasPreviousLeave: true });
      expect(wrapper).toMatchSnapshot();
    });

    it("calls claims.update when user clicks continue", async () => {
      const { appLogic, claim, submitForm } = setup({ hasPreviousLeave: true });
      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          previous_leaves: claim.previous_leaves,
        }
      );
    });

    it("adds another entry when user clicks 'Add another'", async () => {
      const { appLogic, claim, clickAddPreviousLeave, submitForm } = setup({
        hasPreviousLeave: true,
      });

      clickAddPreviousLeave();

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          previous_leaves: [...claim.previous_leaves, new PreviousLeave()],
        }
      );
    });

    it("removes the leave when the user clicks 'Remove' and the leave isn't saved to the API", async () => {
      const {
        appLogic,
        claim,
        clickRemoveFirstPreviousLeave,
        submitForm,
      } = setup({ hasPreviousLeave: true });
      appLogic.benefitsApplications.update.mockImplementationOnce(
        (applicationId, patchData) => {
          expect(applicationId).toBe(claim.application_id);
          expect(patchData.previous_leaves).toHaveLength(1);
        }
      );

      await clickRemoveFirstPreviousLeave();

      await submitForm();

      expect(appLogic.otherLeaves.removePreviousLeave).not.toHaveBeenCalled();
      expect(appLogic.benefitsApplications.update).toHaveBeenCalledTimes(1);
    });

    it("removes the leave when the user clicks 'Remove' and the leave is saved to the API when the DELETE request succeeds", async () => {
      const {
        appLogic,
        claim,
        clickRemoveFirstPreviousLeave,
        submitForm,
      } = setup({ hasPreviousLeave: true });

      claim.previous_leaves[0].previous_leave_id = "mock-employer-leave-id-1";

      appLogic.benefitsApplications.update.mockImplementationOnce(
        (applicationId, patchData) => {
          expect(applicationId).toBe(claim.application_id);
          expect(patchData.previous_leaves).toHaveLength(1);
        }
      );
      await clickRemoveFirstPreviousLeave();

      await submitForm();

      expect(appLogic.otherLeaves.removePreviousLeave).toHaveBeenCalled();
      expect(appLogic.benefitsApplications.update).toHaveBeenCalledTimes(1);
    });

    it("does not remove the leave when the user clicks `Remove` and the DELETE request fails", async () => {
      const {
        appLogic,
        claim,
        clickRemoveFirstPreviousLeave,
        submitForm,
      } = setup({ hasPreviousLeave: true });

      claim.previous_leaves[0].previous_leave_id = "mock-employer-leave-id-1";

      appLogic.otherLeaves.removePreviousLeave.mockImplementationOnce(
        () => false
      );

      appLogic.benefitsApplications.update.mockImplementationOnce(
        (applicationId, patchData) => {
          expect(applicationId).toBe(claim.application_id);
          expect(patchData.previous_leaves).toHaveLength(2);
        }
      );

      await clickRemoveFirstPreviousLeave();
      await submitForm();

      expect(appLogic.otherLeaves.removePreviousLeave).toHaveBeenCalled();
      expect(appLogic.benefitsApplications.update).toHaveBeenCalledTimes(1);
    });

    describe("when the user's claim does not have previous leaves", () => {
      it("adds a blank entry so a card is rendered", () => {
        const { wrapper } = setup({ hasPreviousLeave: false });
        const entries = wrapper.find(RepeatableFieldset).prop("entries");

        expect(entries).toHaveLength(1);
        expect(entries[0]).toEqual(new PreviousLeave());
      });

      it("calls claims.update with newly-entered data when user clicks continue", async () => {
        const { appLogic, claim, submitForm, wrapper } = setup({
          hasPreviousLeave: false,
        });
        const previousLeave = previousLeaves[0];

        // the top-level wrapper doesn't render the PreviousLeaveCard, so we have to dive to cause the components to render
        const previousLeaveWrapper = wrapper
          .find(RepeatableFieldset)
          .dive()
          .find(PreviousLeaveCard)
          .dive();
        const { changeField, changeRadioGroup } = simulateEvents(
          previousLeaveWrapper
        );

        changeRadioGroup(
          "previous_leaves[0].is_for_current_employer",
          previousLeave.is_for_current_employer
        );
        changeRadioGroup(
          "previous_leaves[0].leave_reason",
          previousLeave.leave_reason
        );
        changeField(
          "previous_leaves[0].leave_start_date",
          previousLeave.leave_start_date
        );
        changeField(
          "previous_leaves[0].leave_end_date",
          previousLeave.leave_end_date
        );

        await submitForm();

        expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            previous_leaves: [previousLeave],
          }
        );
      });
    });

    describe("when there are validation errors", () => {
      it.todo("updates the formState with employer_benefit_ids - see CP-1686");
    });
  });
});

const setupPreviousLeaveCard = () => {
  let getFunctionalInputProps;
  const index = 0;
  testHook(() => {
    getFunctionalInputProps = useFunctionalInputProps({
      appErrors: new AppErrorInfoCollection(),
      formState: {},
      updateFields: jest.fn(),
    });
  });

  const wrapper = shallow(
    <PreviousLeaveCard
      employer_fein="12-3456789"
      entry={new PreviousLeave()}
      index={index}
      getFunctionalInputProps={getFunctionalInputProps}
    />
  );

  return { index, wrapper };
};

describe("PreviousLeaveCard", () => {
  it("renders fields for a PreviousLeave instance", () => {
    const { wrapper } = setupPreviousLeaveCard();
    expect(wrapper).toMatchSnapshot();
  });

  it("doesn't include Unknown as a benefit type option", () => {
    const { index, wrapper } = setupPreviousLeaveCard();
    const field = wrapper.find({
      name: `previous_leaves[${index}].leave_reason`,
    });

    expect(field.prop("choices")).not.toContainEqual(
      expect.objectContaining({ value: PreviousLeaveReason.unknown })
    );
  });
});
