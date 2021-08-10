import { EventEmitter } from "events";

export default class Reporter {
  emitter: EventEmitter;

  constructor() {
    this.emitter = new EventEmitter();
  }

  listen(): void {
    this.emitter.on("counter", (...args) => {
      console.log("counter for", args);
    });

    this.emitter.on("histogram", (...args) => {
      console.log("histogram", args);
    });
  }
}
