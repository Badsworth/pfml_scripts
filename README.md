# Massachusetts Paid Family & Medical Leave

This is the top level of the monorepo for the Mass PFML project, including web portal and API. View the `README` in each child directory for information specific to each system component.

## Installation

When initially setting up the project, install packages from the repo root to enable git hooks and linting.

```
npm install
```

## Portal

### Prerequisites

Node v10 (or greater)

### Run Instructions

Run the web portal locally from the project root directory with the following commands:
```
npm install --prefix portal
npm run dev --prefix portal
```

## API

TBD

## Directory Structure

```
└── portal                  🚪 Claimant portal web app
└── infra                   🌲 Infrastructure config
└── docs                    🔖 Developer documentation
```
