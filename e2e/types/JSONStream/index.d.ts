/**
 * Simple typings for JSONStream, which doesn't get its types from @types/jsonstream
 * due to capitalization differences on case-sensitive filesystems.
 */
declare module "JSONStream" {
  export interface Options {
    recurse: boolean;
  }

  export function parse(pattern: any): NodeJS.ReadWriteStream;
  export function parse(patterns: any[]): NodeJS.ReadWriteStream;

  /**
   * Create a writable stream.
   * you may pass in custom open, close, and seperator strings. But, by default,
   * JSONStream.stringify() will create an array,
   * (with default options open='[\n', sep='\n,\n', close='\n]\n')
   */
  /** If you call JSONStream.stringify(false) the elements will only be seperated by a newline. */
  type NewlineOnlyIndicator = false
  export function stringify(): NodeJS.ReadWriteStream;
  export function stringify(newlineOnly: NewlineOnlyIndicator): NodeJS.ReadWriteStream;
  export function stringify(open: string, sep: string, close: string): NodeJS.ReadWriteStream;
  /**
   * Create a writable stream.
   * you may pass in custom open, close, and seperator strings. But, by default,
   * JSONStream.stringify() will create an array,
   * (with default options open='[\n', sep='\n,\n', close='\n]\n')
   */
  export function stringifyObject(): NodeJS.ReadWriteStream;
  export function stringifyObject(open: string, sep: string, close: string): NodeJS.ReadWriteStream;
}
