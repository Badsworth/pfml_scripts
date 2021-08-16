import BaseModel from "./BaseModel";

/** @typedef {import('./Step').default} Step */

/**
 * Model representing a group of Step(s), also referred
 * to as a "Part" (i.e Part 2 of 3).
 */
export default class StepGroup extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'StepGroup' is not ass... Remove this comment to see the full error message
  get defaults() {
    return {
      /**
       * @type {number} Position of this group within the context
       * of all steps (i.e Part 2 of 3)
       */
      number: null,
      /**
       * @type {Step[]}
       */
      steps: [],
    };
  }

  /**
   * Is at least one step in this group active?
   * @returns {boolean}
   */
  get isEnabled() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'steps' does not exist on type 'StepGroup... Remove this comment to see the full error message
    return this.steps.some((step) => !step.isDisabled);
  }
}
