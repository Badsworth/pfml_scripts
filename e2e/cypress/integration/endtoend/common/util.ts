import { ChecklistPage, ReviewPage, ConfirmPage } from "@/pages";

export default function completeApplication(application: Application): void {
  new ChecklistPage()
    .submitClaim(application)
    .enterEmployerInfo(application)
    .reportOtherBenefits(application)
    .addPaymentInfo(application)
    .reviewAndSubmit();
  new ReviewPage().confirmInfo();
  new ConfirmPage().agreeAndSubmit();
}
