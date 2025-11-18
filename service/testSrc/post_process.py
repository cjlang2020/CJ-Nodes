import requests
prompt_id = "67830de5-8ff6-454b-b401-e90edfa37727"
history = requests.get(f"http://localhost:9488/history/{prompt_id}").json()
print("结果:", history[prompt_id]["outputs"])# 获取历史记录

history_key = "67830de5-8ff6-454b-b401-e90edfa37727"
response = requests.get(f"http://localhost:9488/history/{history_key}")
print("结果:", response.json()[history_key]["outputs"])