# API Security

Notes and recommendations on securing the API against common types of attacks.

- [SQL Injection](#sql-injection)

## SQL Injection

SQL Injection is a type of attack where SQL commands are injected into data-plane input in order to modify the execution of predefined SQL commands. This type of attack can allow disclosure of all data on the system, as well as tampering and destruction of data. These types of attacks are considered high-impact severity.


### Mitigation

SQL Injection attacks can be mitigated using defense-in-depth countermeasures, many of which can be (and are) implemented using existing tools in our stack. The following are recommendations for how we can use our existing tools to further mitigate this type of attack.

#### Using OpenAPI specification

Using the OpenAPI specification we define in `openapi.yaml`, we can configure the API to restrict user input, decreasing the opportunities for injection:
- use the most specific [data types](https://swagger.io/docs/specification/data-models/data-types/) possible when defining schema
- when applicable, use [enums](https://swagger.io/docs/specification/data-models/enums/) to specify an allow-list of known values
- use the [pattern keyword](https://swagger.io/docs/specification/data-models/data-types/#pattern) for string inputs to exclude any unneeded (and potentially malicious) characters from input where appropriate ( `<`, `>`, `=` and `;`, for example)

#### Using Application Code

Pydantic and SQLAlchemy provide features that can help mitigate SQL Injection that should be leveraged where SQL injection is possible:
- Pydantic
  - use [validators](https://pydantic-docs.helpmanual.io/usage/validators/) for pydantic model fields that originate as user input and are used to interact with the database
- SQLAlchemy
  - _avoid_ using user input in raw SQL; the SQLAlchemy Query API handles the escaping of special characters and using the input in prepared statements using parameterized queries

#### Using Database Schema

We define our database schema using SQLAlchemy models. It is recommended to use the most specific types available for data columns. This serves as another layer of user input validation, and should mitigate injections that attempt to modify data.


### Other Resources

- [SQL Injection | OWASP](https://owasp.org/www-community/attacks/SQL_Injection)
- [SQL Injection Prevention - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
