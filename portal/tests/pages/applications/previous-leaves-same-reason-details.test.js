import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import PreviousLeave, {
  PreviousLeaveReason,
} from "../../../src/models/PreviousLeave";
import PreviousLeavesSameReasonDetails from "../../../src/pages/applications/previous-leaves-same-reason-details";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = { employer_fein: "12-3456789" }) => {
  const claim = new MockBenefitsApplicationBuilder().continuous().create();

  const { appLogic, wrapper } = renderWithAppLogic(
    PreviousLeavesSameReasonDetails,
    {
      claimAttrs: claimAttrs || claim,
    }
  );

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    claim,
    submitForm,
    wrapper,
  };
};

const previousLeaveData = {
  is_for_current_employer: true,
  is_for_same_reason_as_leave_reason: null,
  leave_end_date: "2021-06-11",
  leave_minutes: 840,
  leave_reason: null,
  leave_start_date: "2021-05-06",
  previous_leave_id: null,
  worked_per_week_minutes: 1920,
};

const setPreviousLeaveFields = (wrapper, previousLeave) => {
  const otherPreviousLeaveDetailsCard = wrapper
    .find("RepeatableFieldset")
    .dive()
    .find("RepeatableFieldsetCard")
    .first()
    .dive()
    .find("PreviousLeaveSameReasonDetailsCard")
    .first()
    .dive();

  const { changeRadioGroup, changeField } = simulateEvents(
    otherPreviousLeaveDetailsCard
  );
  changeRadioGroup(
    "previous_leaves_same_reason[0].is_for_current_employer",
    previousLeave.is_for_current_employer
  );
  changeField(
    "previous_leaves_same_reason[0].leave_start_date",
    previousLeave.leave_start_date
  );
  changeField(
    "previous_leaves_same_reason[0].leave_end_date",
    previousLeave.leave_end_date
  );
  changeField(
    "previous_leaves_same_reason[0].worked_per_week_minutes",
    previousLeave.worked_per_week_minutes
  );
  changeField(
    "previous_leaves_same_reason[0].leave_minutes",
    previousLeave.leave_minutes
  );
};

const clickFirstRemoveButton = async (wrapper) => {
  // can't use simulateEvent's .click() here because this is a Child component
  await wrapper
    .find("RepeatableFieldset")
    .dive()
    .find("RepeatableFieldsetCard")
    .first()
    .dive()
    .find("Button")
    .simulate("click");
};

const clickAddPreviousLeaveButton = async (wrapper) => {
  await wrapper
    .find("RepeatableFieldset")
    .dive()
    .find({ name: "add-entry-button" })
    .simulate("click");
};

const createClaimWithPreviousLeaves = () =>
  new MockBenefitsApplicationBuilder()
    .continuous()
    .employed()
    .previousLeavesSameReason([
      {
        leave_end_date: "2021-01-26",
        leave_minutes: 25,
        leave_reason: PreviousLeaveReason.care,
        leave_start_date: "2021-01-01",
        previous_leave_id: 89,
        worked_per_week_minutes: 40,
      },
      {
        leave_end_date: "2020-12-13",
        leave_minutes: 20,
        leave_reason: PreviousLeaveReason.bonding,
        leave_start_date: "2020-11-21",
        previous_leave_id: 9,
        worked_per_week_minutes: 40,
      },
    ])
    .create();

describe("PreviousLeavesSameReasonDetails", () => {
  describe("when the user has no previous leaves reported", () => {
    it("renders the page", () => {
      const { wrapper } = setup();
      expect(wrapper).toMatchSnapshot();
    });

    it("adds a blank entry so a card is rendered", () => {
      const { wrapper } = setup();
      const entries = wrapper.find("RepeatableFieldset").prop("entries");

      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(new PreviousLeave());
    });

    it("adds an empty previous leave when the user clicks Add Previous Leave", async () => {
      const { wrapper } = setup();
      setPreviousLeaveFields(wrapper, previousLeaveData);
      await clickAddPreviousLeaveButton(wrapper);

      const entries = wrapper.find("RepeatableFieldset").prop("entries");
      expect(entries).toHaveLength(2);
      expect(entries).toEqual([previousLeaveData, new PreviousLeave()]);

      expect(
        wrapper.find("RepeatableFieldset").dive().find("RepeatableFieldsetCard")
      ).toHaveLength(2);
    });

    it("removes a previous leave when user clicks Remove Leave", async () => {
      const { wrapper } = setup();
      setPreviousLeaveFields(wrapper, previousLeaveData);
      await clickAddPreviousLeaveButton(wrapper);

      await clickFirstRemoveButton(wrapper);

      const entries = wrapper.find("RepeatableFieldset").prop("entries");
      expect(entries).toHaveLength(1);
      expect(entries).toEqual([new PreviousLeave()]);

      expect(
        wrapper.find("RepeatableFieldset").dive().find("RepeatableFieldsetCard")
      ).toHaveLength(1);
    });
  });

  describe("when user's claim has previous leaves", () => {
    it("renders the page", () => {
      const claimWithPreviousLeaves = createClaimWithPreviousLeaves();
      const { wrapper } = setup(claimWithPreviousLeaves);
      expect(
        wrapper.find("RepeatableFieldset").dive().find("RepeatableFieldsetCard")
      ).toHaveLength(2);
      expect(wrapper).toMatchSnapshot();
    });

    it("adds an empty previous leave when the user clicks Add Previous Leave", async () => {
      const claimWithPreviousLeaves = createClaimWithPreviousLeaves();
      const { wrapper } = setup(claimWithPreviousLeaves);
      await clickAddPreviousLeaveButton(wrapper);

      const entries = wrapper.find("RepeatableFieldset").prop("entries");
      expect(entries).toHaveLength(3);
      expect(entries).toEqual([
        ...claimWithPreviousLeaves.previous_leaves_same_reason,
        new PreviousLeave(),
      ]);

      expect(
        wrapper.find("RepeatableFieldset").dive().find("RepeatableFieldsetCard")
      ).toHaveLength(3);
    });

    it("removes a previous leave when user clicks Remove Leave", async () => {
      const claimWithPreviousLeaves = createClaimWithPreviousLeaves();
      const { wrapper } = setup(claimWithPreviousLeaves);
      setPreviousLeaveFields(wrapper, previousLeaveData);
      await clickAddPreviousLeaveButton(wrapper);

      await clickFirstRemoveButton(wrapper);

      const entries = wrapper.find("RepeatableFieldset").prop("entries");
      expect(entries).toHaveLength(2);
      expect(entries).toEqual([
        claimWithPreviousLeaves.previous_leaves_same_reason[1],
        new PreviousLeave(),
      ]);
      expect(
        wrapper.find("RepeatableFieldset").dive().find("RepeatableFieldsetCard")
      ).toHaveLength(2);
    });
  });

  it("calls update when user submits form", async () => {
    const { appLogic, wrapper } = setup();
    const spy = jest.spyOn(appLogic.benefitsApplications, "update");

    const { submitForm } = simulateEvents(wrapper);
    await submitForm();
    expect(spy).toHaveBeenCalledTimes(1);
  });
});
