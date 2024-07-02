from nodeodm_client import NodeodmClient

for i in range(5):
    nodeodm_client = NodeodmClient()
    nodeodm_client.calculate_orthophoto()
