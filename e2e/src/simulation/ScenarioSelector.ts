import { PortalApplicationSubmission } from "./types";

type ApplicationGenerator = () => PortalApplicationSubmission;

/**
 * This class implements "Roulette Wheel Selection" to select a generator based on probability.
 *
 * See https://www.codewars.com/kata/567b21565ffbdb30e3000010 for a nice visual
 * of this algorithm.
 */
export default class ScenarioSelector {
  private generators: {
    generator: ApplicationGenerator;
    probability: number;
  }[];
  private wheel?: number[];

  constructor() {
    this.generators = [];
  }
  add(probability: number, generator: ApplicationGenerator): this {
    this.generators.push({ probability, generator });
    // Clear the wheel when something is added.
    this.wheel = undefined;

    return this;
  }
  private generateWheel() {
    // Build up a "roulette wheel" consisting of array indices from this.generators.
    // Each generator gets N slices, where N = the generator's probability.
    // Slices are combined to form the final wheel.
    return this.generators.reduce((partial, { probability }, i) => {
      const slices = new Array(probability).fill(i);
      return partial.concat(slices);
    }, [] as number[]);
  }
  spin(): PortalApplicationSubmission {
    // Generate the wheel on demand.
    let wheel;
    if (this.wheel) {
      wheel = this.wheel;
    } else {
      wheel = this.wheel = this.generateWheel();
    }

    const sliceIdx = Math.floor(Math.random() * wheel.length);
    const idx = wheel[sliceIdx];

    return this.generators[idx].generator();
  }
}
