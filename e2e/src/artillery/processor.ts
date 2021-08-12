import { EventEmitter } from "events";
import ArtilleryPFMLInteractor, {
  ArtilleryContext,
} from "./ArtilleryInteractor";
import Reporter from "./Reporter";

const interactor = new ArtilleryPFMLInteractor();
const reporter = new Reporter();
reporter.listen();

function fn(
  cb: (context: ArtilleryContext, ee: EventEmitter) => Promise<void>
) {
  return async function (
    context: ArtilleryContext,
    ee: EventEmitter,
    done: DoneCB
  ) {
    try {
      await cb(context, ee);
      done();
    } catch (e) {
      console.error(e);
      done(e);
    }
  };
}

type DoneCB = (err?: Error) => void;

export const submitAndAdjudicate = fn(
  async (context: ArtilleryContext, ee: EventEmitter) => {
    await interactor.generateClaim(context, ee, "LSTBHAP1");
    await interactor.submitClaim(context, ee);
    await interactor.postProcessClaim(context, ee);
    console.log("Done generating claim", context.claim?.scenario);
  }
);
