import { Readable } from "stream";

export default interface FileWrapper {
  filename: string;
  asStream(): NodeJS.ReadableStream;
  asUInt8Array(): Uint8Array;
}

export class Uint8ArrayWrapper {
  constructor(private data: Uint8Array, public filename: string) {}

  asStream(): NodeJS.ReadableStream {
    // @todo: Do we actually need a buffer here?
    return Readable.from(Buffer.from(this.data));
  }
  asUInt8Array(): Uint8Array {
    return this.data;
  }
}

export class StreamWrapper implements FileWrapper {
  constructor(private stream: NodeJS.ReadableStream, public filename: string) {}
  asStream(): NodeJS.ReadableStream {
    return this.stream;
  }
  asUInt8Array(): Uint8Array {
    return new Uint8Array([]);
  }
}
