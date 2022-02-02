import { stringer } from "stream-json/Stringer";
import { disassembler } from "stream-json/Disassembler";
import { parser } from "stream-json/Parser";
import { chain } from "stream-chain";

/**
 * Handlers for reading/writing a JSON array in a stream.
 */
export function stringify() {
  return chain([disassembler(), stringer({ makeArray: true })]);
}

export function parse() {
  return parser();
}
