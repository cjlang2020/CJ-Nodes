import requests
import json

# 读取 workflow JSON
with open("D:/AI/comfyui_custom_nodes/CJ-Nodes/service/testSrc/SDXL文生图.json", "r", encoding="utf-8") as f:
    workflow = json.load(f)

# 发送 POST 请求
response = requests.post(
    "http://localhost:9488/prompt",
    json={"prompt": workflow}
)
print(response.json())
# 获取 prompt_id 并查询结果
prompt_id = response.json()["prompt_id"]
history = requests.get(f"http://localhost:9488/history/{prompt_id}").json()
print("结果:", history[prompt_id]["outputs"])