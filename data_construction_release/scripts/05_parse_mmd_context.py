import copy
import re
import spacy
import os
import pandas as pd
import json

def normalize_alnum(s):
    return re.sub(r'[^A-Za-z0-9]', '', (s or "")).lower()

def count_key(section_title: str, key: str):
    count = 0
    section_title = section_title.lstrip()
    while count < len(section_title) and section_title[count] == key:
        count += 1
    
    return count

def split_by_sections(content: str):
    HASH = '#'
    ret = list()
    contents = content.split('\n\n')

    section_cache = list()
    for c in contents:
        c = c.strip()
        if not c:
            continue
        if c.startswith(HASH):
            section_level = count_key(c, HASH)
            if len(section_cache) == 0:
                section_cache.append([section_level, c])
            else:
                if section_cache[-1][0] == 6:      
                    section_cache = list()
                while len(section_cache) and section_cache[-1][0] >= section_level:
                    section_cache.pop()
                section_cache.append([section_level, c])

        else:
            if c[0].islower():
                i = len(ret) - 1
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
            else:
                ret.append([copy.deepcopy(section_cache), c])
    
    return ret

def scoring(text, span) -> int:
    preceding_token, next_token = '', ''
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

    preceding_token = preceding_token.lower()
    next_token = next_token.lower()

    preceding_token = preceding_token.lstrip('(')
    next_token = next_token.rstrip(')')
    
    score = 0

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
            if len(m) == 1:
                m = m + [len(text)]
            if '/' in text[m[0]:m[1]]:
                span[1] = m[1]
                continue
            break

    return text[span[0]:span[1]]

if os.getenv("DATASET_PARSER_CPU") != "1":
    spacy.require_gpu()
nlp = spacy.load('en_core_web_trf')

def parse(splited_content):
    url_pattern = re.compile(r'((https?|ftp)://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s()]*)?(?<!\.))')
    for i in range(len(splited_content)):
        m = url_pattern.findall(splited_content[i][1])
        if m:
            urls = [j[0] for j in m]
            urls = [modify_url(url, splited_content[i][1]) for url in urls]

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

                    numbers = list(re.finditer(r'\d{1,3}(?:,\d{3})*', splited_content[target_paragraph_idx][1]))
                    candidate_spans = [number.span() for number in numbers if number.group() == footnote_num]
                    scores = [scoring(splited_content[target_paragraph_idx][1], candidate_span) for candidate_span in candidate_spans]

                        
                    if len(candidate_spans) == 0:
                        url = splited_content[i][1].replace(f'Footnote {footnote_num}: ', '').strip().replace(' ', '')
                        splited_content[i][1] = f'Footnote {footnote_num}: {url}'
                        continue

                    decision = sorted(zip(candidate_spans, scores), key=lambda x: x[1], reverse=True)[0][0]
                    splited_content[target_paragraph_idx][1] = splited_content[target_paragraph_idx][1][:decision[0]] + f'[FOOTNOTE_{footnote_num}_URL_CITE]' + splited_content[target_paragraph_idx][1][decision[1]:]

                    url = splited_content[i][1].replace(f'Footnote {footnote_num}: ', '').strip().replace(' ', '')
                    splited_content[i][1] = f'Footnote {footnote_num}: {url}'
                else:
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
                    
                    numbers = list(re.finditer(r'\d{1,3}(?:,\d{3})*', splited_content[target_paragraph_idx][1]))
                    candidate_spans = [number.span() for number in numbers if number.group() == footnote_num]
                    scores = [scoring(splited_content[target_paragraph_idx][1], candidate_span) for candidate_span in candidate_spans]
                    if len(candidate_spans) == 0:
                        continue
                    decision = sorted(zip(candidate_spans, scores), key=lambda x: x[1], reverse=True)[0][0]
                    splited_content[target_paragraph_idx][1] = splited_content[target_paragraph_idx][1][:decision[0]] + f'[FOOTNOTE_{footnote_num}]' + splited_content[target_paragraph_idx][1][decision[1]:]

                    for url in urls:
                        url = url.replace(' ', '')
                        splited_content[i][1] = splited_content[i][1].replace(url, f'{url}').strip()
            else:
                for url in urls:
                    url = url.replace(' ', '')
                    splited_content[i][1] = splited_content[i][1].replace(url, f'{url}').strip()
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
                
                numbers = list(re.finditer(r'\d{1,3}(?:,\d{3})*', splited_content[target_paragraph_idx][1]))
                candidate_spans = [number.span() for number in numbers if number.group() == footnote_num]
                scores = [scoring(splited_content[target_paragraph_idx][1], candidate_span) for candidate_span in candidate_spans]
                if len(candidate_spans) == 0:
                    continue
                decision = sorted(zip(candidate_spans, scores), key=lambda x: x[1], reverse=True)[0][0]
                splited_content[target_paragraph_idx][1] = splited_content[target_paragraph_idx][1][:decision[0]] + f'[FOOTNOTE_{footnote_num}]' + splited_content[target_paragraph_idx][1][decision[1]:]

    return splited_content


reference_titles = [
    'reference', 'references', 'bibliography',
    'bibliographic reference', 'bibliographic references',
]

count = 0
pt_cs_ci_dict = {}
url_pattern = re.compile(
    r'((?:https?|ftp)://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s()]*)?(?<!\.))'
)
for parent, dirs, files in os.walk('data/mmd'):
    for file in files:
        if not file.endswith('.mmd'):
            continue

        print(f'{count}: {file}', end='\r')
        try:
            with open(parent + '/' + file, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            print('error:', file)
            continue

        splited_content = split_by_sections(content)
        splited_content = parse(splited_content)

        citation_paragraphs = []
        for c in splited_content:
            if len(c[0]) == 0 or c[1] == '':
                continue
            if url_pattern.search(c[1]) or re.search(r'FOOTNOTE_(\d+)', c[1]):
                citation_paragraphs.append(c)

        if not citation_paragraphs:
            continue

        count += 1
        paper_title = file.replace('.mmd', '')
        pt_cs_ci_dict[paper_title] = []

        for c in citation_paragraphs:
            section_titles = c[0]
            paragraph_text = c[1]
            new_section_titles = [i[1].replace('#', '') for i in section_titles]
            
            v = paragraph_text
            v = re.sub(
                r"_\[((https?|ftp)://[^\]]*?)(?:_)\]\(\1(?:_)?\)",
                r"[\1](\1)",
                v
            )
            pattern = r"\[(https?|ftp)://[^\]]+\]\((https?|ftp)://[^\)]+\)"
            replacement = lambda m: re.search(r"(https?|ftp)://[^\]]+", m.group()).group().strip("])")
            v = re.sub(pattern, replacement, v)
            paragraph_text = v

            record_base = {
                "Passage-title": new_section_titles,
                "Citation-paragraph": paragraph_text,
                "Citation-sentence": "",
                "Citation-info": "",
                "Citation-type": "Body",
                "URL": ""
            }

            for sent in nlp(paragraph_text).sents:
                sent_text = str(sent)
                if url_pattern.search(sent_text) or re.search(r'FOOTNOTE_\d+', sent_text):
                    rec = record_base.copy()
                    rec["Citation-sentence"] = sent_text
                    pt_cs_ci_dict[paper_title].append(rec)


        footnote_map = {}
        for record in pt_cs_ci_dict[paper_title]:
            match = re.search(r'Footnote (\d+): ', record["Citation-paragraph"])      
            if match:
                footnote_num = match.group(1)
                footnote_map[footnote_num] = record["Citation-paragraph"]   

        new_records = []   
        for other in pt_cs_ci_dict[paper_title]:
            footnote_match = re.search(r'FOOTNOTE_(\d+)', other["Citation-sentence"])
            if footnote_match:
                footnote_num = footnote_match.group(1)
                if footnote_num in footnote_map:
                    other["Citation-type"] = "Footnote"
                    footnote_map[footnote_num] = re.sub(
                        r"Footnote\s*(\d*):",
                        lambda m: (m.group(1) + " ") if m.group(1) else "",
                        footnote_map[footnote_num]
                    )
                    other["Citation-info"] = footnote_map[footnote_num]

                    url_match = url_pattern.findall(footnote_map[footnote_num])
                    if url_match:
                        cleaned_urls = [u.split("<<")[0].strip().rstrip("]") for u in url_match]
                        cleaned_urls = list(set(cleaned_urls)) 

                        if len(cleaned_urls) > 1:
                            for url in cleaned_urls:
                                new_record = other.copy()
                                new_record["URL"] = url
                                new_records.append(new_record)  
                            other["URL"] = cleaned_urls[0]
                        else:
                            cleaned_url = cleaned_urls[0]
                            other["URL"] = cleaned_url

        pt_cs_ci_dict[paper_title].extend(new_records)

                            
        before_len = len(pt_cs_ci_dict[paper_title])
        pt_cs_ci_dict[paper_title] = [
            rec for rec in pt_cs_ci_dict[paper_title]
            if not rec["Citation-sentence"].startswith("Footnote ") and not rec["Citation-paragraph"].startswith("Footnote ")
        ]
        after_len = len(pt_cs_ci_dict[paper_title])
        print(f"Removed {before_len - after_len} Footnote-only records from {paper_title}")

        expanded_all = []  

        for record in pt_cs_ci_dict[paper_title]:
            passage_titles = record.get("Passage-title", [])
            if passage_titles:
                titles_text = " ".join(str(t).lower() for t in passage_titles if len(t) > 1)
                if any(ref in titles_text for ref in reference_titles) and record["Citation-type"] != "Footnote":
                    record["Citation-type"] = "Reference"

            expanded_records = []  

            for f in ("Citation-paragraph", "Citation-sentence"):
                v = record.get(f)
                if v:
                    v = v.replace('\r', ' ').replace('\n', ' ').strip()
                    v = re.sub(r'\s+', ' ', v)
                    record[f] = v

            for i in ["Citation-paragraph", "Citation-sentence", "Citation-info"]:
                v = record.get(i)
                if v:
                    v = re.sub(
                        r"_\[((https?|ftp)://[^\]]*?)(?:_)\]\(\1(?:_)?\)",
                        r"[\1](\1)",
                        v
                    )
                    record[i] = v

            pattern = r"\[(https?|ftp)://[^\]]+\]\((https?|ftp)://[^\)]+\)"
            replacement = lambda m: re.search(r"(https?|ftp)://[^\]]+", m.group()).group().strip("])")
            for i in ["Citation-paragraph", "Citation-sentence", "Citation-info"]:
                v = record.get(i)
                if v:
                    new_v = re.sub(pattern, replacement, v)
                    record[i] = new_v

            text = record.get("Citation-sentence", "")
            if text and record["Citation-type"] != "Footnote":
                url_match = url_pattern.findall(text)
                if len(url_match) > 1:
                    print(f"===WOW! two or more URLs are found in {paper_title}===")
                if url_match:
                    cleaned_urls = [u.split("<<")[0].strip().rstrip("]") for u in url_match]
                    cleaned_urls = list(set(cleaned_urls))  

                    for url in cleaned_urls:
                        new_record = record.copy()
                        new_record["URL"] = url
                        expanded_records.append(new_record)
                else:
                    expanded_records.append(record)
            elif text and record["Citation-type"] == "Footnote":       
                expanded_records.append(record)
                url_match = url_pattern.findall(text)
                if url_match:
                    cleaned_urls = [u.split("<<")[0].strip().rstrip("]") for u in url_match]
                    cleaned_urls = list(set(cleaned_urls))  

                    for url in cleaned_urls:
                        new_record = record.copy()
                        new_record["URL"] = url
                        new_record["Citation-type"] = "Body"
                        new_record["Citation-info"] = ""
                        expanded_records.append(new_record)
            else:
                expanded_records.append(record)
            expanded_all.extend(expanded_records)

            for rec in expanded_all:
                cit_type = rec.get("Citation-type", "")
                paragraph = rec.get("Citation-paragraph", "")
                sentence = rec.get("Citation-sentence", "")
                info = rec.get("Citation-info","")
                url = rec.get("URL", "")

                if not url:
                    continue
                
                if cit_type == "Body":
                    if f"{url}[Cite]" not in paragraph and url in paragraph:
                        paragraph = paragraph.replace(url, f"{url}[Cite]")
                    if f"{url}[Cite]" not in sentence and url in sentence:
                        sentence = sentence.replace(url, f"{url}[Cite]")
                elif cit_type == "Footnote":              
                    paragraph_match = re.findall(r'FOOTNOTE_(\d+)', paragraph)
                    sentence_match = re.search(r'FOOTNOTE_(\d+)', sentence)
                    if sentence_match:
                        fn_num = sentence_match.group(1)
                        for i in paragraph_match:
                            if fn_num == i:
                                p_fn_num = i
                        paragraph = re.sub(rf'\[?FOOTNOTE_{fn_num}\]?', f"[Cite_Footnote_{fn_num}]", paragraph)
                        sentence = re.sub(rf'\[?FOOTNOTE_{fn_num}\]?', f"[Cite_Footnote_{fn_num}]", sentence)

                else:
                    if f"{url}[Cite_Ref]" not in paragraph and url in paragraph:
                        paragraph = paragraph.replace(url, f"{url}[Cite_Ref]")
                    if f"{url}[Cite_Ref]" not in sentence and url in sentence:
                        sentence = sentence.replace(url, f"{url}[Cite_Ref]")

                paragraph = re.sub(r'\[?FOOTNOTE_(\d+)?\]?', '', paragraph)
                sentence = re.sub(r'\[?FOOTNOTE_(\d+)?\]?', '', sentence)
                info = re.sub(r'\[?FOOTNOTE_(\d+)?\]?', '', info)

                rec["Citation-paragraph"] = paragraph
                rec["Citation-sentence"] = sentence
                rec["Citation-info"] = info

            for rec in expanded_all:
                titles = rec.get("Passage-title", [])
                paper_title_norm = paper_title.strip().lower()
                cleaned_titles = []
                abstract_index = None

                for t in titles:
                    t_norm = normalize_alnum(t)
                    if t_norm == paper_title_norm:
                        continue
                    cleaned_titles.append(t)

                titles = cleaned_titles

                for idx, t in enumerate(titles):
                    if t.strip().lower() == "abstract":
                        abstract_index = idx
                        break

                if abstract_index is not None:
                    if len(titles) > abstract_index+1:
                        titles = titles[abstract_index + 1:]
                    else:
                        titles = ["Abstract"]

                rec["Passage-title"] = titles
            pt_cs_ci_dict[paper_title] = expanded_all

        print(f"\n{paper_title}: {len(pt_cs_ci_dict[paper_title])} records after URL expansion")

no_citation_paragraph_count = sum(
    1 for papers in pt_cs_ci_dict.values() for r in papers
    if r["Citation-sentence"] and not r["Citation-paragraph"]
)
print("引用段落文が追加できていない物の数：", no_citation_paragraph_count)
print("URL周辺情報が取得できた数：", len(pt_cs_ci_dict))

with open("data/intermediate/pt_cs_ci_dict_output.json", "w", encoding="utf-8") as f:
    json.dump(pt_cs_ci_dict, f, ensure_ascii=False, indent=2)