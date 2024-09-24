import os

def write_file(path,text):
    with open(path,'w',encoding='utf-8') as f:
        f.write(text)


def sliding_window_split(text, window_size=1024, overlap_size=768):
    start = 0
    end = window_size
    chunks = []

    while end-256 <= len(text):
        chunks.append(text[start:end])
        start += (window_size - overlap_size)
        end = start + window_size

    return chunks

import json
def list_to_jsonl(input_list, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in input_list:
            json_line = json.dumps(item, ensure_ascii=False)
            f.write(json_line + '\n')
def main():
    datas = []
    files = os.listdir(r'D:\projects\pythonproject\YmirAI\trainning\video_ocr\z_done')
    files = [ fr"D:\projects\pythonproject\YmirAI\trainning\video_ocr\z_done\{i}" for i in files]
    for i in files:
        with open(i,"r",encoding="utf-8") as f:
            text = f.read()
        text = text.replace("(","（").replace(")","）") \
            .replace(":","：") \
            .replace("---\n","").replace(" ","")

        print(i,len(text))
        write_file(os.path.join("datasets/cleaned",os.path.basename(i)),text)
        text_list = sliding_window_split(text)
        print([len(i) for i in text_list])
        datas.extend( [{"text":i} for i in text_list] )

    print(len(datas))
    list_to_jsonl(datas,"pretraining_data_juchang.jsonl")

if __name__ == '__main__':
    main()
