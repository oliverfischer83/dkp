import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Specify the local endpoint for DynamoDB (default is http://localhost:8000)
dynamodb_endpoint = "http://localhost:8000"

# Create a DynamoDB client
dynamodb = boto3.resource("dynamodb", endpoint_url=dynamodb_endpoint, region_name="localhost")

# Define table name and schema
table_name = "ExampleTable"
key_schema = [{"AttributeName": "ExampleKey", "KeyType": "HASH"}]  # HASH denotes the partition key
attribute_definitions = [{"AttributeName": "ExampleKey", "AttributeType": "S"}]  # 'S' denotes string type

# Specify provisioned throughput for the table (adjust as needed)
provisioned_throughput = {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}

# # Create
# table = dynamodb.create_table(
#     TableName=table_name, KeySchema=key_schema, AttributeDefinitions=attribute_definitions, ProvisionedThroughput=provisioned_throughput
# )
# print(f"Table '{table_name}' created successfully!")

# # Insert
# item_to_insert = {"ExampleKey": "1", "ExampleAttribute": "Sample Data"}
# response = table.put_item(Item=item_to_insert)
# print(f"Item inserted successfully: {response}")

# Read
table = dynamodb.Table("ExampleTable")

response = table.get_item(Key={"ExampleKey": "1"})
item = response.get("Item")
if item:
    print(f"Data read from the table: {item}")
else:
    print("Item not found in the table.")
