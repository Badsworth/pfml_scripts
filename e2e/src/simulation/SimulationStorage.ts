import { SimulationClaim } from "./types";
import fs from "fs";
import path from "path";

/**
 * This class abstracts the directory structure of the simulation.
 */
export default class SimulationStorage {
  directory: string;
  constructor(directory: string) {
    this.directory = directory;
  }
  async claims(): Promise<SimulationClaim[]> {
    const content = await fs.promises.readFile(this.claimFile);
    return JSON.parse(content.toString("utf-8"));
  }
  async users(): Promise<SimulationClaim[]> {
    const content = await fs.promises.readFile(this.usersFile);
    return JSON.parse(content.toString("utf-8"));
  }
  get usersFile(): string {
    return path.join(this.directory, "users.json");
  }
  get stateFile(): string {
    return path.join(this.directory, "state.json");
  }
  get claimFile(): string {
    return path.join(this.directory, "claims.json");
  }
  get mailDirectory(): string {
    return path.join(this.directory, "mail");
  }
  get documentDirectory(): string {
    return path.join(this.directory, "documents");
  }
}
