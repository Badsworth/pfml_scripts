# Software Architecture

This page describes the software architecture and design patterns used for the Portal.

## Overview

The primary design pattern used in the Portal is [Model-View-Controller](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller), which is the design pattern most commonly used whenever designing any application with a user interface.

## Data Models

Not to be confused with the "Model" in Model-View-Controller (MVC), data models represent concepts in the context of the PFML program and the Portal. Data models are used throughout business logic and controller logic, but are not used by lower level View components which should be domain agnostic. Data models should only represent data and not have any business logic or behavior or have any dependencies outside of data models (with the possible exception of simple helper functions).

## App

The [App](/portal/src/pages/_app.js) is the "Controller" for the application and is the effective entry point to the application as directed by the Nextjs framework. The App controls web application logic, what state to pass to pages, and how to handle application events like submitting claims. Top level application logic should live here.

## Pages

[Page components](/portal/src/pages/) are the primary "Controller" unit of the application and represent a single page of the user experience. Page components are the lowest level "Controller" in our application (with the exception of more complex View components that have their own nested MVC pattern). Page components control which "View" components to render, what state to pass to the components to render, and what event handlers to use to handle "View" events.

## Components

[Components](/portal/src/components/) are the primary "View" unit of the application. Simple components simply render data that is passed to them, and exposes events that parent components (the view's controller) can listen to. More complex components can themselves act as controllers and have their own models and nested controllers/views.

The [QuestionPage](/portal/src/components/QuestionPage.js) component is an example of a more complex component that includes a back button and a "Save and Continue" button with onSave and onContinue events that can be listened to.

## API

The API module is reponsible for application-level business logic. This represents the top level "Model" in the MVC design pattern. This includes starting claims, submitting claims, identity proofing, setting payment preferences, etc.

## State Hooks

State hooks are modules used by various components to define and update the state of the application. These hooks represent the "Model" in the MVC design pattern and should not have any knowledge of controller or view code.

An example of a state hook is [useFormState](/portal/src/hooks/useFormState.js).

## Event Hooks

Event hooks are modules that define functions to handle view events. These modules attach view events to the appropriate model update functions, and are the glue that allows us to keep "Model" and "View" decoupled from each other.

Examples of event hooks include [useHandleInputChange](/portal/src/hooks/useHandleInputChange.js) and [useAppLogic](/portal/src/hooks/useAppLogic.js).

## Dependencies

To help prevent technical debt, when adding new modules, consider adding assertions to [dependencies.test.js](/portal/tests/dependencies.test.js) to restrict where the module is used, or what dependencies the new module is allowed to have.

## Services

Services expose functionality that offers a coherent feature / addresses a business need (e.g. `services/featureFlags.js`). A rule of thumb to use is that services are things that could conceptually be turned into separate microservices. In practice, some of these will actually be served by external services and others will not. Examples include caching, translation/localization, validation, authentication, and any APIs. For example, in our codebase we already have these services:

- Error monitoring: uses external New Relic API, so this is an "actual" service
- Feature flags: these don't use an external APIs in this implementation but instead just uses the browser APIs (cookies) to accomplish the task. We could conceivably refactor this module to rely on an external API though. For example [LaunchDarkly](https://launchdarkly.com/) is precisely a product that offers "feature flags as a service" but for now we're just using a homegrown "feature flags service")

## Utilities

Utilities (`utils`) on the other hand are lightweight functions that are useful but don't really offer any business value on their own. They often fall into the category of filling in gaps of the programming language like manipulating strings or other simple data structures that the language itself doesn't offer functions for, and for which we don't feel the need to introduce a separate library/dependency for. A rule of thumb to use for utilities is that they should be generally small and standalone i.e. they shouldn't have any non-trivial dependencies (like external APIs or large libraries).
