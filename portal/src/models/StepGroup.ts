import BaseModel from "./BaseModel";

/** @typedef {import('./Step').default} Step */

/**
 * Model representing a group of Step(s), also referred
 * to as a "Part" (i.e Part 2 of 3).
 */
export default class StepGroup extends BaseModel {
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
    return this.steps.some((step) => !step.isDisabled);
  }
}
