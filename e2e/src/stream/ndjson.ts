import { stringer } from "stream-json/jsonl/Stringer";
import { parser } from "stream-json/jsonl/Parser";
import { chain } from "stream-chain";

/**
 * Handlers for reading/writing an NDJSON array in a stream.
 */
export function stringify() {
  return stringer();
}

export function parse() {
  return chain([
    parser(),
    // Pick off the value, as that's all we care about.
    (item) => item.value,
  ]);
}
