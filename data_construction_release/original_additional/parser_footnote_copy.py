import copy
import re
import spacy
import os
import pandas as pd
import json

# 見出し文字の「#」を数える関数
def count_key(section_title: str, key: str):
    count = 0
    section_title = section_title.lstrip()
    while count < len(section_title) and section_title[count] == key:
        count += 1
    
    return count

# テキスト全体をセクションごとに分割する関数
# [[[2, ## 3 Dataset and Experiment Setup],[3, ### Experiment Setup],For Contextual word embeddngs,~]]
def split_by_sections(content: str):
    HASH = '#'
    ret = list()
    contents = content.split('\n\n')

    section_cache = list()
    for c in contents:
        c = c.strip()
        if not c:
            continue
        # 見出しの追加
        if c.startswith(HASH):
            section_level = count_key(c, HASH)
            if len(section_cache) == 0:
                section_cache.append([section_level, c])
            else:
                if section_cache[-1][0] == 6:       # mdファイルのセクションレベルの最大値？
                    section_cache = list()
                while len(section_cache) and section_cache[-1][0] >= section_level:
                    section_cache.pop()
                section_cache.append([section_level, c])
        # 見出し以外の文（本文，脚注，図，表など）の追加
        else:
            # 先頭が小文字なら直前の文に追加
            if c[0].islower():
                i = len(ret) - 1
                # 直前の文が図，脚注，表ならさらに前の文へ, Table Tab はこの判定じゃ無理（「Table 1:~」という文とlatex形式の文との間に空行がないため、「Table」から文章が始まらない「\\begin{table}」から始まるもの。とかでもいいかも）
                # 本文だが「Figure」や「Table」から始まる場合もあるかもしれないので、これらを除外するのは正しいとは限らない
                while i > 0 and (ret[i][1].startswith('Figure ') or ret[i][1].startswith('Footnote ') or ret[i][1].startswith('Table ') or ret[i][1].startswith('Tab ') or ret[i][1].startswith('Fig ')):   
                    i -= 1
                if i == -1:
                    i = 0
                if len(ret) == 0:
                    if len(section_cache):
                        section_cache[-1][1] += ' ' + c
                    else:
                        section_cache.append([1, '# ' + c])
                else:
                    ret[i] = [ret[i][0], ret[i][1] + ' ' + c]
            # 先頭が大文字なら新しい文として追加
            else:
                ret.append([copy.deepcopy(section_cache), c])
    
    return ret

# ある部分文字列（span で指定）前後の単語や記号を調べて、その文字列が「文中の自然なURL／参照であるかどうか」をスコア化
def scoring(text, span) -> int:
    preceding_token, next_token = '', ''
    # span[0]の直前の単語を取得
    if ' ' not in text[:span[0]]:
        if span[0] > 0:
            preceding_token = text[:span[0]]
    else:
        m = list(re.finditer(r' ', text[:span[0]]))
        m = [i.span()[0] for i in m]
        if span[0] - 1 not in m:
            preceding_token = text[m[-1]+1:span[0]]
        else:
            if len(m) == 1:
                m = [0] + m
            preceding_token = text[m[-2]+1:m[-1]]
    
    # span[1]の直後の単語を取得
    if ' ' not in text[span[1]:]:
        if span[1] < len(text):
            next_token = text[span[1]:]
    else:
        m = list(re.finditer(r' ', text[span[1]:]))
        m = [i.span()[0] + span[1] for i in m]
        # print(m)
        if span[1] not in m:
            next_token = text[span[1]:m[0]]
        else:
            if len(m) == 1:
                m = m + [len(text)]
            next_token = text[m[0]:m[1]]
    # すべて小文字化     
    preceding_token = preceding_token.lower()
    next_token = next_token.lower()
    # 括弧を削除
    preceding_token = preceding_token.lstrip('(')
    next_token = next_token.rstrip(')')
    
    # スコア計算, URLや脚注の参照として不自然な場合は減点
    score = 0
    # preceding_token, next_token の両方にバックスラッシュが含まれている場合は減点（LaTeXのコマンドの可能性が高い）
    # 直前の単語が table, tab., figure, fig., section, sec., equation, eq., algorithm, line, version, ver. の場合は減点（これらは通常URLや脚注参照の直前には来ない）
    # 直前の単語が1文字の場合は減点（a, Iなどは通常URLや脚注参照の直前には来ない）
    # 直前の単語がピリオド(.)またはカンマ(,)で終わる場合は加点（文の終わりにURLや脚注参照が来ることはよくある）
    # ただし、直前の単語がピリオドで終わり、その直前の文字が数字の場合は減点（小数点の可能性があるため）
    # 直前の単語がハイフン(-)で終わる場合は減点（単語の途中で改行されている可能性があるため）
    # 直前の単語が数字で終わる場合は減点（脚注番号の可能性があるため）
    # 次の単語が空文字、改行(\n)、ピリオド(.), カンマ(,), パーセント(%)の場合は加点（文の終わりにURLや脚注参照が来ることはよくある）
    # 次の単語がハイフン(-)で始まる場合は  減点（単語の途中で改行されている可能性があるため）
    if preceding_token in ['table', 'tab.', 'figure', 'fig.', 'section', 'sec.', 'equation', 'eq.', 'algorithm', 'line', 'version', 'ver.'] or len(preceding_token) == 1:
        score -= 1
    elif preceding_token.endswith('.') or preceding_token.endswith(','):
        if preceding_token.endswith('.') and len(preceding_token) > 1 and preceding_token[-2].isdecimal():
            score -= 1
        else:
            score += 1

    if preceding_token.endswith('-') or (len(preceding_token) and preceding_token[-1].isdecimal()):
        score -= 1
        
    if next_token == '' or next_token in ['\n', '.', ',', '%']:
        score += 1

    if next_token.startswith('-'):
        score -= 1

    if '\\' in preceding_token and '\\' in next_token:
        score -=1 
    
    return score


def modify_url(url, text):
    # print(url)
    # print(text)
    # print(url in text)
    # m = re.search(url, text)
    # print(m)
    start = text.find(url)
    span = [start, start + len(url)]

    while True:
        if ' ' not in text[span[1]:]:
            if span[1] < len(text):
                if '/' in text[span[1]:]:
                    span[1] = len(text)
            break
        else:
            m = list(re.finditer(r' ', text[span[1]:]))
            m = [i.span()[0] + span[1] for i in m]
            # print(m)
            # if span[1] not in m:
            #     next_token = text[span[1]:m[0]]
            #     if '/' in text[span[1]:m[0]]:
            #         span[1] = m[0]
            #         continue
            # else:
            if len(m) == 1:
                m = m + [len(text)]
            if '/' in text[m[0]:m[1]]:
                span[1] = m[1]
                continue
            break

    return text[span[0]:span[1]]

spacy.require_gpu()
nlp = spacy.load('en_core_web_trf')

def parse(splited_content):
    # url_pattern = re.compile(r'((https?|ftp)://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?(?<!\.))')
    url_pattern = re.compile(r'((https?|ftp)://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s()]*)?(?<!\.))')
    # url_pattern = re.compile(r'((https?|ftp)://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s()]*)?)(?=\s|$|\.)')
    # url_pattern = re.compile(r'((https?|ftp)://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s().]*)?)(?<!\.)')
    for i in range(len(splited_content)):
        m = url_pattern.findall(splited_content[i][1])
        if m:
            urls = [j[0] for j in m]
            # print(urls)
            urls = [modify_url(url, splited_content[i][1]) for url in urls]
            # print(urls)
            
            # check if footnote
            footnote_pattern = re.compile(r'Footnote (\d+): ')
            footnote_m = footnote_pattern.match(splited_content[i][1])
            
            if footnote_m:
                footnote_num = footnote_m.groups()[0]
                if splited_content[i][1].replace(f'Footnote {footnote_num}: ', '').strip() in urls:
                    target_paragraph_idx = i-1
                    skip_patterns = [
                        re.compile(r'Footnote (\d+): '),
                        re.compile(r'Figure (\d+): '),
                        re.compile(r'Table (\d+): '),
                    ]
                    while target_paragraph_idx > 0:
                        f = False
                        for skip_pattern in skip_patterns:
                            tmp_m = skip_pattern.match(splited_content[target_paragraph_idx][1])
                            if tmp_m or splited_content[target_paragraph_idx][1] == '':
                                target_paragraph_idx -=1
                                f = True
                                break
                        if not f:
                            break
                    
                    # print(splited_content[target_paragraph_idx][1])
                    # numbers, candidate_spans, scores = [], [], []
                    # while target_paragraph_idx > -1 and len(candidate_spans) == 0:
                    #     numbers = list(re.finditer(r'\d{1,3}(?:,\d{3})*', splited_content[target_paragraph_idx][1]))
                    #     candidate_spans = [number.span() for number in numbers if number.group() == footnote_num]
                    #     scores = [scoring(splited_content[target_paragraph_idx][1], candidate_span) for candidate_span in candidate_spans]
                    #
                    #     target_paragraph_idx -= 1
                    numbers = list(re.finditer(r'\d{1,3}(?:,\d{3})*', splited_content[target_paragraph_idx][1]))
                    candidate_spans = [number.span() for number in numbers if number.group() == footnote_num]
                    scores = [scoring(splited_content[target_paragraph_idx][1], candidate_span) for candidate_span in candidate_spans]

                        
                    if len(candidate_spans) == 0:
                        url = splited_content[i][1].replace(f'Footnote {footnote_num}: ', '').strip().replace(' ', '')
                        splited_content[i][1] = f'Footnote {footnote_num}: <<url>>{url}<</url>>'
                        continue
                    # print(candidate_spans)
                    # print(scores)
                    # print(candidate_spans)
                    # print(scores)
                    decision = sorted(zip(candidate_spans, scores), key=lambda x: x[1], reverse=True)[0][0]
                    splited_content[target_paragraph_idx][1] = splited_content[target_paragraph_idx][1][:decision[0]] + f'[FOOTNOTE_{footnote_num}_URL_CITE]' + splited_content[target_paragraph_idx][1][decision[1]:]
                    # for number in numbers[::-1]:
                    #     if number.group() == footnote_num:
                    #         splited_content[target_paragraph_idx][1] = splited_content[target_paragraph_idx][1][:number.span()[0]] + '[URL_CITE]' + splited_content[target_paragraph_idx][1][number.span()[1]:]
                    # splited_content[i][1] = splited_content[i][1].replace(f'Footnote {footnote_num}: ', f'Footnote {footnote_num}: <<url>>') + '<</url>>'
                    # splited_content[i][1] = ''
                    url = splited_content[i][1].replace(f'Footnote {footnote_num}: ', '').strip().replace(' ', '')
                    splited_content[i][1] = f'Footnote {footnote_num}: <<url>>{url}<</url>>'
                else:
                    # splited_content[i][1] = re.sub(footnote_pattern, '', splited_content[i][1]).strip()
                    target_paragraph_idx = i-1
                    skip_patterns = [
                        re.compile(r'Footnote (\d+): '),
                        re.compile(r'Figure (\d+): '),
                        re.compile(r'Table (\d+): '),
                    ]
                    while target_paragraph_idx > 0:
                        f = False
                        for skip_pattern in skip_patterns:
                            tmp_m = skip_pattern.match(splited_content[target_paragraph_idx][1])
                            if tmp_m or splited_content[target_paragraph_idx][1] == '':
                                target_paragraph_idx -=1
                                f = True
                                break
                        if not f:
                            break
                    
                    # print(splited_content[target_paragraph_idx][1])
                    numbers = list(re.finditer(r'\d{1,3}(?:,\d{3})*', splited_content[target_paragraph_idx][1]))
                    candidate_spans = [number.span() for number in numbers if number.group() == footnote_num]
                    scores = [scoring(splited_content[target_paragraph_idx][1], candidate_span) for candidate_span in candidate_spans]
                    # print(candidate_spans)
                    # print(scores)
                    if len(candidate_spans) == 0:
                        continue
                    decision = sorted(zip(candidate_spans, scores), key=lambda x: x[1], reverse=True)[0][0]
                    splited_content[target_paragraph_idx][1] = splited_content[target_paragraph_idx][1][:decision[0]] + f'[FOOTNOTE_{footnote_num}]' + splited_content[target_paragraph_idx][1][decision[1]:]

                    for url in urls:
                        url = url.replace(' ', '')
                        splited_content[i][1] = splited_content[i][1].replace(url, f'[URL_CITE]<<url>>{url}<</url>>').strip()
            else:
                for url in urls:
                    url = url.replace(' ', '')
                    splited_content[i][1] = splited_content[i][1].replace(url, f'[URL_CITE]<<url>>{url}<</url>>').strip()
        else:
            footnote_pattern = re.compile(r'Footnote (\d+): ')
            footnote_m = footnote_pattern.match(splited_content[i][1])
            
            if footnote_m:
                footnote_num = footnote_m.groups()[0]
                target_paragraph_idx = i-1
                skip_patterns = [
                    re.compile(r'Footnote (\d+): '),
                    re.compile(r'Figure (\d+): '),
                    re.compile(r'Table (\d+): '),
                ]
                while target_paragraph_idx > 0:
                    f = False
                    for skip_pattern in skip_patterns:
                        tmp_m = skip_pattern.match(splited_content[target_paragraph_idx][1])
                        if tmp_m or splited_content[target_paragraph_idx][1] == '':
                            target_paragraph_idx -=1
                            f = True
                            break
                    if not f:
                        break
                
                # print(splited_content[target_paragraph_idx][1])
                numbers = list(re.finditer(r'\d{1,3}(?:,\d{3})*', splited_content[target_paragraph_idx][1]))
                candidate_spans = [number.span() for number in numbers if number.group() == footnote_num]
                scores = [scoring(splited_content[target_paragraph_idx][1], candidate_span) for candidate_span in candidate_spans]
                # print(candidate_spans)
                # print(scores)
                if len(candidate_spans) == 0:
                    continue
                decision = sorted(zip(candidate_spans, scores), key=lambda x: x[1], reverse=True)[0][0]
                splited_content[target_paragraph_idx][1] = splited_content[target_paragraph_idx][1][:decision[0]] + f'[FOOTNOTE_{footnote_num}]' + splited_content[target_paragraph_idx][1][decision[1]:]

    return splited_content

# main
# URLの完全一致で比較して、一致した部分の節タイトルや段落文などを追加する,重複したURLは節タイトル、引用文の数だけ増やす（これによりProduce, non-Produceの数が若干増えそう）
reference_titles = [
    'reference',
    'references',
    'bibliography',
    'bibliographic reference',
    'bibliographic references',
]

count = 0

pt_cs_ci_dict = {}
for parent, dirs, files in os.walk('/workspace/2025-0829-making_dataset/mmd'):
    for file in files:
        if file.endswith('.mmd'):

            if os.path.exists(parent.replace('mmd', 'parsed_csvs')+'/'+file.replace('mmd', 'csv')):
                count += 1
                continue
            print(f'{count}: {file}', end='\r')
            try:
                with open(parent+'/'+file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                print('error:', file)
            splited_content = split_by_sections(content)
            splited_content = parse(splited_content)

            output_contents = list()
            for c in splited_content:
                is_ref = [sec[1].strip('#').strip().lower() in reference_titles for sec in c[0]]
                if len(c[0]) == 0:
                    continue
                # 参考文献をスキップ
                # elif any(is_ref):
                #     continue
                elif c[1] == '':
                    continue
                # elif '\\begin{' in c[1] and '\\end{' in c[1]:
                #     continue
                else:
                    for sent in nlp(c[1]).sents:
                        sent = str(sent)
                        if len(sent.split()) < 5 and not sent.startswith('Footnote') and not sent.startswith('Figure') and not sent.startswith('Table') and len(output_contents) > 0:
                            if '='.join([s[1] for s in output_contents[-1][0]]) == '='.join([s[1] for s in c[0]]):
                                output_contents[-1][1] += sent
                                continue
                        output_contents.append([
                            c[0],
                            sent
                        ])

            if len(output_contents):
                section_titles, sentence = map(list, zip(*output_contents))
            else:
                continue

            count += 1
            # 節タイトル、引用文、脚注文を格納する大きな辞書
            
            footnote_url_list = []
            footnote_token_list = []
            footnote_num_list = []
            paragraph_url_list = []
            paragraph_footnote_num_list = []
            paragraph_footnote_url_list = []
            paragraph_footnote_token_list = []
            reference_url_list = []
            # ファイルごとの処理ループ中で以下を実行
            try:
                # 論文タイトル（拡張子なし）をキーにする
                paper_title = file.replace('.mmd', '')
                pt_cs_ci_dict[paper_title] = []

                # 値は [section_titles, sentence]
                df = pd.DataFrame(data={
                    'Passage-title': section_titles,
                    'Citation-sentence': sentence,
                })
                df_url_list = df.to_dict(orient="records")

                # <<url>> を含む段落を抽出
                for i in splited_content:
                    if "<<url>>" in i[1]:
                        match = re.search(r'Footnote (\d+): ', i[1])
                        if match:
                            paragraph_footnote_url_list.append(i)
                        paragraph_url_list.append(i)

                # <<url>> を含む文を抽出
                for record in df_url_list:
                    if "<<url>>" in record["Citation-sentence"]:
                        match = re.search(r'Footnote (\d+): ', record["Citation-sentence"])
                        if match:
                            footnote_num_list.append(match.group(1))
                            footnote_url_list.append(record)
                        pt_cs_ci_dict[paper_title].append(record)

                # FOOTNOTE番号を含む文を抽出
                for record in df_url_list:
                    for num in footnote_num_list:
                        if f"FOOTNOTE_{num}" in record["Citation-sentence"]:
                            footnote_token_list.append(record)
                            break  # 1件見つかれば次の record へ
                    else:
                        continue

                # FOOTNOTE番号を含む段落を抽出
                for i in splited_content:
                    for num in footnote_num_list:
                        if f"FOOTNOTE_{num}" in i[1]:
                            paragraph_footnote_token_list.append(i)
                            break  # 1件見つかれば次の record へ
                    else:
                        continue

                # Citation-type と Citation-info を付与
                for record in pt_cs_ci_dict[paper_title]:
                    record["Citation-info"] = ""
                    record["Citation-type"] = "Body"
                    record["Citation-paragraph"] = ""
                    record["URL"] = ""
                    # Citation-paragraph追加(ここ怪しい)
                    for i in paragraph_url_list:
                        if record["Citation-sentence"] != "" and record["Citation-sentence"] in i[1]:
                            record["Citation-paragraph"] = i[1]
                            break

                    match = re.search(r'Footnote (\d+): ', record["Citation-sentence"])
                    if match:
                        record["Citation-info"] = record["Citation-sentence"]
                        record["Citation-type"] = "Footnote"
                        footnote_num = match.group(1)

                        # Footnote と対応する token を置換
                        for token in footnote_token_list:
                            if f"FOOTNOTE_{footnote_num}" in token["Citation-sentence"]:
                                record["Citation-sentence"] = token["Citation-sentence"]
                                record["Passage-title"] = token["Passage-title"]
                                break
                        for ptoken in paragraph_footnote_token_list:
                            if f"FOOTNOTE_{footnote_num}" in ptoken[1]:
                                record["Citation-paragraph"] = ptoken[1]

                    # Reference セクションを検出
                    for ref in reference_titles:
                        passage_titles = record.get("Passage-title", [])
                        if not passage_titles:
                            continue

                        # Passage-title のどこかに "references" などが含まれているか？
                        titles_text = " ".join(str(t[1]).lower() for t in passage_titles if len(t) > 1)
                        if ref in titles_text and "<<url>>" in record.get("Citation-sentence", ""):
                            record["Citation-type"] = "Reference"
                            record["Citation-info"] = record["Citation-sentence"]
                            record["Citation-sentence"] = ""
                    # URL抽出用の正規表現パターン
                    url_pattern = re.compile(r'((?:https?|ftp)://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s()]*)?(?<!\.))')
                    urls = url_pattern.findall(text)

                    clean_urls = []
                    for url in urls:
                        # <<以降を削除
                        url = url.split("<<")[0]
                        # 2. 末尾の [] を削除
                        if url.endswith("]"):
                            url = url[:-1]
                        clean_urls.append(url)
                    # Citation-sentence, Citation-info, Citation-Paragraphの順で探索
                    for field in ["Citation-sentence", "Citation-info"]:
                        text = record.get(field, "")
                        if not text:
                            continue

                        url_match = url_pattern.findall(text)
                        if url_match:
                            # 最初に見つかったURLを採用
                            raw_url = url_match[0].strip()

                            # 「<<」以降を削除
                            cleaned_url = raw_url.split("<<")[0]
                            # 末尾に「]」がある場合は除去
                            if cleaned_url.endswith("]"):
                                cleaned_url = cleaned_url[:-1]
                            # 両端の空白除去
                            cleaned_url = cleaned_url.strip()

                            record["URL"] = cleaned_url

                            break  # 優先順位の高い順に処理するため、見つかったら終了

            except Exception as e:
                print('error:', file, e)

        print(len(pt_cs_ci_dict[paper_title]))
        print(len(footnote_url_list))
        print(len(footnote_token_list))
        print(len(paragraph_url_list))
        print(len(paragraph_footnote_url_list))
        print(len(paragraph_footnote_token_list))
        # for i in pt_cs_ci_dict[paper_title]:
        #     if i["Citation-paragraph"]:
        #         print(1)


# print(pt_cs_ci_dict)
no_citation_paragraph_count = 0
for i in pt_cs_ci_dict.values():
    for j in i:
        if j["Citation-sentence"] != "" and j["Citation-paragraph"] == "":
            no_citation_paragraph_count += 1
print("引用段落文が追加できていない物の数：",no_citation_paragraph_count)
print("URL周辺情報が取得できた数：",len(pt_cs_ci_dict))

# jsonファイルに記述
with open("/workspace/2025-0829-making_dataset/parser/pt_cs_ci_dict_output.json", "w", encoding="utf-8") as f:
    json.dump(pt_cs_ci_dict, f, ensure_ascii=False, indent=2) 

            # os.makedirs(parent.replace('mmd', 'parsed_csvs'), exist_ok=True)

            
            # try:
            #     df.to_csv(parent.replace('mmd', 'parsed_csvs')+'/'+file.replace('.mmd', '.csv'), index=False)
            # except:
            #     print('error:', file)

# with open('/workspace/2025-0829-making_dataset/mmd/_A Passage to India__ Pre-trained Word Embeddings for Indian Languages.mmd', 'r', encoding='utf-8') as f:
#     content = f.read()
# splited_content = split_by_sections(content)
# splited_content = parse(splited_content)

# print(splited_content)