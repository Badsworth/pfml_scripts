# Naming conventions

## Field names

Input and model field names should match the API field names, which means they should be formatted as snake case.

| ✅ Like this | 🛑 Not like this |
| ------------ | ---------------- |
| `first_name` | `firstName`      |

Benefits

- Eliminates the need for additional code to convert a Portal naming style to the API naming style
- Consistent with what the field names would need to be if we were submitting the data directly through the HTML `<form>` rather than through JS.
