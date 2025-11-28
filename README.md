# Azure Science Quiz - Production Starter

Production-ready starter for a 10-question online science quiz using Azure Static Web Apps + Azure Functions.

Features:
- Frontend: static HTML + JS (hosted on Azure Static Web Apps)
- Backend: Azure Function (Python) with HTTP trigger
- Storage: Azure Table Storage for responses (consumption-friendly)
- CI/CD: GitHub Actions using `Azure/static-web-apps-deploy`
- Local dev: `local.settings.json` example for Functions Core Tools

## Quickstart (high level)
1. Create an Azure Static Web App in the portal (Free tier) and connect your repo.
2. Create an Azure Storage Account and a Table called `QuizResponses`.
3. Add the Storage connection string to Static Web App secrets:
   - Name: `AZURE_TABLE_CONN` Value: `<your_storage_connection_string>`
4. Push to `main` branch — the GitHub Action will deploy frontend & API.
5. Open the Static Web App URL, run a test submission.

## Local development
- Install Azure Functions Core Tools and Python 3.11+ (matching the function runtime).
- Copy `local.settings.json.example` to `local.settings.json` and paste your storage connection string.
- From repo root:
  ```
  cd api
  pip install -r requirements.txt
  func start
  ```

## Repo layout
- frontend/      => static site (index.html + app.js + questions.json)
- api/SubmitFunction => Azure Function (Python)
- .github/workflows => GitHub Actions deploy workflow

