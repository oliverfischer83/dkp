import boto3
import os
from dotenv import load_dotenv

load_dotenv()

print("test aws")

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.environ["AWS_REGION"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
)

table = dynamodb.Table("test")

# table.put_item(
#    Item={
#       "part_key": "2",
#       "sort_key": "2",
#       "Artist": "No One You Know 2",
#       "SongTitle": "Call Me Today 2", 
#       "AlbumTitle": "Somewhat Famous 2",
#       "Awards": 2
#    }
# )

resoponse = table.get_item(Key={"part_key": "2","sort_key": "2"})
print("Response:\n")
print(resoponse)

if "Item" in resoponse:
   item = resoponse["Item"]
   print(f"Item: {item}")
else:
   print("Item not found")



