import { Readable } from "stream";
import path from "path";

export default interface FileWrapper {
  filename: string;
  asStream(): NodeJS.ReadableStream;
  asUInt8Array(): Uint8Array;
}

type ReadableStreamWithFilename = Readable & { path: string };

export class Uint8ArrayWrapper {
  constructor(private data: Uint8Array, public filename: string) {}

  asStream(): NodeJS.ReadableStream {
    const strm = Readable.from(
      Buffer.from(this.data)
    ) as ReadableStreamWithFilename;
    // There must be a path property on the stream in order for form-data to detect the
    // mime type properly. Make a dummy path here - this doesn't really exist, at this
    // point the whole file is only contained in memory.
    strm.path = path.join(__dirname, this.filename);
    return strm;
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
    throw new Error(
      "This method is not implemented. Cannot convert from stream to UInt8Array."
    );
  }
}
