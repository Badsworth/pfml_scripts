## Experian SOAP Address Verification API

The Experian SOAP Address Verification API (V3) is documented [here](https://docs.experianaperture.io/address-validation/address-validate-soap/api-reference/api-specification/#v3-endpoint).

Since the WSDL had import of non secure XSDs, we had an issue running the API from our ECS tasks which all have SSL requirements. This folder contains local versions of the WSDL and associated XSDs. We have adjusted our code to consume these local files by default.