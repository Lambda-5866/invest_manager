import requests

url = "https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService/getGoldPriceInfo"

params = {
    "serviceKey" : "d197cbc79911b5cdc1bd69a9bbee490d30ca8c955d84ae9793984c701752fbe1",
    "resultType" : "json"
}

res = requests.get(url, params=params)

print(res.text)