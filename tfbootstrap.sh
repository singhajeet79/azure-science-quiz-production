# 1. Set variables
RG_NAME="rg-azure-science-quiz-production"
STG_ACCOUNT_NAME="azurequizprodsa"
CONTAINER_NAME="tfstate"
LOCATION="centralindia" # Must match your defined location

# 2. Create the Resource Group (if it doesn't exist)
az group create --name $RG_NAME --location $LOCATION

# 3. Create the Storage Account (if it doesn't exist)
# Note: You may need a different account name if 'azurequizprodsa' is already taken globally.
az storage account create \
  --resource-group $RG_NAME \
  --name $STG_ACCOUNT_NAME \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# 4. Create the 'tfstate' Container
az storage container create \
  --name $CONTAINER_NAME \
  --account-name $STG_ACCOUNT_NAME
