import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import PreviousLeave, {
  PreviousLeaveReason,
} from "../../../src/models/PreviousLeave";
import PreviousLeavesOtherReasonDetails from "../../../src/pages/applications/previous-leaves-other-reason-details";
import React from "react";
import { shallow } from "enzyme";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs) => {
  const claim = new MockBenefitsApplicationBuilder()
    .employed()
    .continuous()
    .create();

  const { appLogic, wrapper } = renderWithAppLogic(
    PreviousLeavesOtherReasonDetails,
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
  leave_end_date: "2021-06-11",
  leave_minutes: 840,
  leave_reason: PreviousLeaveReason.medical,
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
    .find("PreviousLeavesOtherReasonDetailsCard")
    .first()
    .dive();

  const { changeRadioGroup, changeField } = simulateEvents(
    otherPreviousLeaveDetailsCard
  );
  changeRadioGroup(
    "previous_leaves_other_reason[0].leave_reason",
    previousLeave.leave_reason
  );
  changeRadioGroup(
    "previous_leaves_other_reason[0].is_for_current_employer",
    previousLeave.is_for_current_employer
  );
  changeField(
    "previous_leaves_other_reason[0].leave_start_date",
    previousLeave.leave_start_date
  );
  changeField(
    "previous_leaves_other_reason[0].leave_end_date",
    previousLeave.leave_end_date
  );
  changeField(
    "previous_leaves_other_reason[0].worked_per_week_minutes",
    previousLeave.worked_per_week_minutes
  );
  changeField(
    "previous_leaves_other_reason[0].leave_minutes",
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
    .employed()
    .continuous()
    .previousLeavesOtherReason([
      {
        leave_end_date: "2021-01-26",
        leave_minutes: 1500,
        leave_reason: PreviousLeaveReason.care,
        leave_start_date: "2021-01-01",
        previous_leave_id: 89,
        worked_per_week_minutes: 2400,
      },
      {
        leave_end_date: "2020-12-13",
        leave_minutes: 1200,
        leave_reason: PreviousLeaveReason.bonding,
        leave_start_date: "2020-11-21",
        previous_leave_id: 9,
        worked_per_week_minutes: 2400,
      },
    ])
    .create();

const createClaimWithPreviousLeaves_care = () =>
  new MockBenefitsApplicationBuilder()
    .caringLeaveReason()
    .continuous()
    .employed()
    .previousLeavesOtherReason([
      {
        leave_end_date: "2021-01-26",
        leave_minutes: 1500,
        leave_reason: PreviousLeaveReason.care,
        leave_start_date: "2021-01-01",
        previous_leave_id: 89,
        worked_per_week_minutes: 2400,
      },
      {
        leave_end_date: "2020-12-13",
        leave_minutes: 1200,
        leave_reason: PreviousLeaveReason.bonding,
        leave_start_date: "2020-11-21",
        previous_leave_id: 9,
        worked_per_week_minutes: 2400,
      },
    ])
    .create();

describe("PreviousLeavesOtherReasonDetails", () => {
  describe("when the user has no previous leaves reported", () => {
    let wrapper;

    beforeEach(() => {
      ({ wrapper } = setup());
    });

    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
    });

    it("adds a blank entry so a card is rendered", () => {
      const entries = wrapper.find("RepeatableFieldset").prop("entries");

      expect(entries).toHaveLength(1);
      expect(entries[0]).toEqual(new PreviousLeave());
    });

    it("adds an empty previous leave when the user clicks Add Previous Leave", async () => {
      setPreviousLeaveFields(wrapper, previousLeaveData);
      await clickAddPreviousLeaveButton(wrapper);

      const entries = wrapper.find("RepeatableFieldset").prop("entries");
      expect(entries).toHaveLength(2);
      expect(entries).toEqual([
        new PreviousLeave({ ...previousLeaveData }),
        new PreviousLeave(),
      ]);

      expect(
        wrapper.find("RepeatableFieldset").dive().find("RepeatableFieldsetCard")
      ).toHaveLength(2);
    });

    it("removes a previous leave when user clicks Remove Leave", async () => {
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
    let claimWithPreviousLeaves;
    let wrapper;

    beforeEach(() => {
      claimWithPreviousLeaves = createClaimWithPreviousLeaves();
      ({ wrapper } = setup(claimWithPreviousLeaves));
    });

    it("renders the page", () => {
      const cards = wrapper
        .find("RepeatableFieldset")
        .dive()
        .find("RepeatableFieldsetCard");
      const firstCard = cards
        .find("PreviousLeavesOtherReasonDetailsCard")
        .first()
        .dive();
      const InputHoursHint = () =>
        firstCard.find("InputHours").first().prop("hint");
      const inputHoursHint = shallow(<InputHoursHint />);

      expect(cards).toHaveLength(2);
      expect(wrapper).toMatchSnapshot();
      expect(firstCard).toMatchSnapshot();
      expect(inputHoursHint.find("Trans").dive()).toMatchSnapshot();

      expect(wrapper.find("Hint")).toMatchInlineSnapshot(`
        <Hint
          className="margin-bottom-3"
        >
          Enter details about each period of leave taken between January 1, 2021 and January 1, 2021. A leave period begins on the day you first went on leave and ends on the last day of leave. If you were on leave intermittently, your leave period begins on the first day you went on leave and ends on the very last day.
        </Hint>
      `);
    });

    it("changes hint date when leave reason is caring leave", () => {
      const claimWithPreviousLeaves_care = createClaimWithPreviousLeaves_care();
      const { wrapper } = setup(claimWithPreviousLeaves_care);

      expect(wrapper.find("Hint")).toMatchInlineSnapshot(`
        <Hint
          className="margin-bottom-3"
        >
          Enter details about each period of leave taken between July 1, 2021 and January 1, 2021. A leave period begins on the day you first went on leave and ends on the last day of leave. If you were on leave intermittently, your leave period begins on the first day you went on leave and ends on the very last day.
        </Hint>
      `);
    });

    it("adds an empty previous leave when the user clicks Add Previous Leave", async () => {
      await clickAddPreviousLeaveButton(wrapper);

      const entries = wrapper.find("RepeatableFieldset").prop("entries");
      expect(entries).toHaveLength(3);
      expect(entries).toEqual([
        ...claimWithPreviousLeaves.previous_leaves_other_reason,
        new PreviousLeave(),
      ]);

      expect(
        wrapper.find("RepeatableFieldset").dive().find("RepeatableFieldsetCard")
      ).toHaveLength(3);
    });

    it("removes a previous leave when user clicks Remove Leave", async () => {
      setPreviousLeaveFields(wrapper, previousLeaveData);
      await clickAddPreviousLeaveButton(wrapper);

      await clickFirstRemoveButton(wrapper);

      const entries = wrapper.find("RepeatableFieldset").prop("entries");
      expect(entries).toHaveLength(2);
      expect(entries).toEqual([
        claimWithPreviousLeaves.previous_leaves_other_reason[1],
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
