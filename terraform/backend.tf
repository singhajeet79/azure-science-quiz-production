terraform {
  backend "azurerm" {
    # ⚠️ Replace these values with your actual backend storage details
    resource_group_name  = "rg-azure-science-quiz-production" 
    storage_account_name = "azurequizprodsa" # Must be globally unique
    container_name       = "tfstate"
    key                  = "quiz-app.tfstate"
  }
}
