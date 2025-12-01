# Set the required AzureRM provider version
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# Define the Azure provider
provider "azurerm" {
  features {}
}

# --- 1. Variable Definitions ---
variable "resource_group_name" {
  description = "Name for the Azure Resource Group."
  default     = "rg-azure-science-quiz-production"
}

variable "location" {
  description = "Azure region for deployment (India Central)."
  default     = "centralindia"
}

variable "app_prefix" {
  description = "Base prefix for globally unique resources (Storage, Function App)."
  default     = "azurequizprod" # Keep short for unique names
}

variable "table_name" {
  description = "The name of the Azure Table to store quiz results."
  default     = "QuizResponses"
}

# --- 2. Resource Group ---
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

# --- 3. Storage Account (Used for Function Code & Static Frontend) ---
resource "azurerm_storage_account" "main" {
  name                     = "${var.app_prefix}sa"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS" # Using LRS for cost savings in development/non-critical environments
  
  # Enable Static Website Hosting for the frontend files (index.html, app.js, etc.)
  static_website {
    index_document = "index.html"
    error_404_document = "404.html"
  }
}

# --- 4. Azure Table Storage for Quiz Results ---
resource "azurerm_storage_table" "quiz_results" {
  name                 = var.table_name
  storage_account_name = azurerm_storage_account.main.name
}

# --- 5. App Service Plan (Consumption / Serverless) ---
resource "azurerm_service_plan" "function_app_plan" {
  name                = "${var.app_prefix}-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux" # Required for Python Functions
  sku_name            = "Y1"    # Consumption Plan (Serverless)
}

# --- 6. Function App (Backend API) ---
resource "azurerm_linux_function_app" "submit_api" {
  name                = "${var.app_prefix}-api"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.function_app_plan.id
  storage_account_name = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key

// 🔥 REQUIRED FIX: Add the site_config block
  site_config {
    # Set the desired Python version for the Function App
    application_stack {
      python_version = "3.10" # Use a supported Python version (e.g., 3.10)
    }
  }

  
  # Python Runtime Configuration
  app_settings = {
    # Standard function settings
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "WEBSITE_RUN_FROM_PACKAGE" = "1" # Use package deployment
    
    # Environment variables used in __init__.py
    # 1. Connection string for Azure Table Storage
    "AZURE_TABLE_CONN" = azurerm_storage_account.main.primary_connection_string
    # 2. Table name used in __init__.py
    "AZURE_TABLE_NAME" = azurerm_storage_table.quiz_results.name
  }
}

# --- 7. Outputs ---
output "frontend_url" {
  description = "The URL for the static website endpoint."
  value       = azurerm_storage_account.main.primary_web_endpoint
}

output "function_endpoint" {
  description = "The base URL for the Azure Function App API."
  value       = azurerm_linux_function_app.submit_api.default_hostname
}
