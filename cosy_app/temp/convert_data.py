

with open(r'C:\Users\wwwwi\AppData\Local\Temp\MicrosoftEdgeDownloads\a82c38d3-beff-4144-864b-268772a1b9cc\6分钟带你了解《尘白禁区》世界观.srt','r',encoding='utf-8') as f:
    text = f.read()

p = text.split("\n\n")

for  i in p:
    text = i.split("\n")
    print(text[2])