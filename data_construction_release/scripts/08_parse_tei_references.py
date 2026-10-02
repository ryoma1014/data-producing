import copy
import re
import spacy
import os
import pandas as pd
import json
import xml.etree.ElementTree as ET
from itertools import zip_longest
from lxml import etree as ET_LXML  
def extract_bibl_info_as_dict(bibl, ns):
    """
    Extract structured bibliographic information from <biblStruct> as a dictionary.
    Each field corresponds to a logical part (author, title, journal, etc.)
    """

    info = {
        "authors": [],
        "titles": [],
        "monograph_titles": [],
        "publishers": [],
        "publication_years": [],
        "dois": [],
        "urls": [],
        "full_text": ""
    }

    # === Authors ===
    authors = bibl.findall(".//tei:analytic/tei:author", ns)
    for author in authors:
        author_text = " ".join(" ".join(author.itertext()).split())
        if author_text:
            info["authors"].append(author_text)

    # === Article Titles ===
    titles = bibl.findall(".//tei:analytic/tei:title", ns)
    for t in titles:
        title_text = " ".join(" ".join(t.itertext()).split())
        if title_text:
            info["titles"].append(title_text)

    # === Journal / Monograph Titles ===
    monogr_titles = bibl.findall(".//tei:monogr/tei:title", ns)
    for mt in monogr_titles:
        mt_text = " ".join(" ".join(mt.itertext()).split())
        if mt_text:
            info["monograph_titles"].append(mt_text)

    # === Publishers ===
    publishers = bibl.findall(".//tei:monogr/tei:imprint/tei:publisher", ns)
    for pub in publishers:
        pub_text = " ".join(" ".join(pub.itertext()).split())
        if pub_text:
            info["publishers"].append(pub_text)

    # === Publication Years ===
    dates = bibl.findall(".//tei:monogr/tei:imprint/tei:date", ns)
    for date in dates:
        if "when" in date.attrib:
            info["publication_years"].append(date.attrib["when"])
        else:
            date_text = " ".join(" ".join(date.itertext()).split())
            if date_text:
                info["publication_years"].append(date_text)

    # === DOIs ===
    dois = bibl.findall(".//tei:idno[@type='DOI']", ns)
    for doi in dois:
        doi_text = " ".join(" ".join(doi.itertext()).split())
        if doi_text:
            info["dois"].append(doi_text)

    # === URLs ===
    ptrs = bibl.findall(".//tei:ptr[@target]", ns)
    for p in ptrs:
        url = p.attrib.get("target", "").strip()
        if url:
            info["urls"].append(url)

    # === Full Text (raw biblStruct text) ===
    all_text = " ".join(" ".join(bibl.itertext()).split())
    info["full_text"] = all_text

    return info

# # === 追加 ===
# # lxml版を使う場合はこちらをインポート


# def extract_references_from_xml_lxml(xml_folder):
#     """
#     lxml を使用した高速・堅牢版
#     - ElementTree版と同じ処理を行うが、lxmlの getparent() により parent_map が不要
#     """
#     global para_count, no_para_count, sen_count, no_sen_count, para_no_sen_count, url_count, url_set_count

#     xml_ref_dict = {}

#     for parent, dirs, files in os.walk(xml_folder):
#         for file in files:
#             if not file.endswith(".xml"):
#                 continue
#             file_path = os.path.join(parent, file)

#             try:
#                 parser = ET_LXML.XMLParser(recover=True)        # 重複するxml:idをスキップ
#                 tree = ET_LXML.parse(file_path,parser)  # === lxml変更点 ===
#                 root = tree.getroot()
#             except Exception as e:
#                 print(f"XML parse error in {file}: {e}")
#                 continue

#             ns = {"tei": "http://www.tei-c.org/ns/1.0"}

#             bibl_structs = root.findall(".//tei:listBibl/tei:biblStruct", namespaces=ns)
#             ref_records = []
#             all_urls = []

#             bibl_id_to_urls = {}
#             bibl_id_to_text = {}

#             for bibl in bibl_structs:
#                 bibl_id = bibl.attrib.get("{http://www.w3.org/XML/1998/namespace}id", "")

#                 bibl_text = extract_bibl_info_as_dict(bibl, ns)
#                 if bibl_text:
#                     bibl_id_to_text[bibl_id] = bibl_text

#                 urls = bibl.findall(".//tei:ptr[@target]", namespaces=ns)
#                 for url_elem in urls:
#                     url = url_elem.attrib.get("target", "").strip()
#                     if not url.startswith(("http", "https", "ftp")):
#                         continue
#                     all_urls.append(url)
#                     if bibl_id:
#                         bibl_id_to_urls.setdefault(bibl_id, []).append(url)

#             url_count += len(all_urls)
#             url_set_count += len(set(all_urls))

#             paragraphs = root.findall(".//tei:text//tei:body//tei:p", namespaces=ns)

#             url_to_paragraphs = {}
#             url_to_sentences = {}
#             url_to_titles = {}

#             for p in paragraphs:
#                 paragraph_parts = []
#                 for elem in p.iter():
#                     if elem.tag == f"{{{ns['tei']}}}ref" and elem.attrib.get("type") == "bibr":
#                         ref_text = "".join(elem.itertext()).strip()
#                         paragraph_parts.append(ref_text)
#                     elif elem.text and elem.tag != f"{{{ns['tei']}}}ref":
#                         paragraph_parts.append(elem.text)
#                     if elem.tail:
#                         paragraph_parts.append(elem.tail)

#                 paragraph_text = "".join(paragraph_parts).replace("\n", " ").replace("\t", " ").strip()
#                 if not paragraph_text:
#                     continue

#                 refs = p.findall(".//tei:ref[@type='bibr']", namespaces=ns)
#                 if not refs:
#                     continue

#                 # === lxml変更点: 親階層を getparent() で探索 ===
#                 section_titles = []
#                 seen = set()

#                 ancestor = p
#                 current_head = None
#                 while ancestor is not None:
#                     head = ancestor.find("./tei:head[@n]", namespaces=ns)
#                     if head is None:
#                         head = ancestor.find("./tei:head", namespaces=ns)
#                     if head is not None:
#                         current_head = head
#                         break
#                     ancestor = ancestor.getparent()  # === lxml変更点 ===

#                 if current_head is not None:
#                     n_value = current_head.attrib.get("n", "").strip()
#                     head_text = "".join(current_head.itertext()).strip()

#                     if n_value:
#                         section_titles.append(f"{n_value} {head_text}")
#                         seen.add(f"n:{n_value}")
#                     elif head_text:
#                         section_titles.append(head_text)
#                         seen.add(f"text:{head_text}")

#                     # === lxml変更点: 親タイトルを getparent() でたどる ===
#                     if n_value:
#                         parts = n_value.split(".")
#                         while len(parts) > 1:
#                             parts = parts[:-1]
#                             parent_n = ".".join(parts)

#                             ancestor = current_head.getparent()  # === lxml変更点 ===
#                             while ancestor is not None:
#                                 parent_head = ancestor.find(f"./tei:head[@n='{parent_n}']", namespaces=ns)
#                                 if parent_head is not None:
#                                     parent_text = "".join(parent_head.itertext()).strip()
#                                     full_title = f"{parent_n} {parent_text}"
#                                     key = f"n:{parent_n}"
#                                     if key not in seen:
#                                         section_titles.insert(0, full_title)
#                                         seen.add(key)
#                                     break
#                                 ancestor = ancestor.getparent()  # === lxml変更点 ===

#                 section_title = section_titles

#                 doc = nlp(paragraph_text)
#                 sentence_texts = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
#                 sentence_spans = [
#                     {"start": sent.start_char, "end": sent.end_char, "text": sent.text.strip()}
#                     for sent in doc.sents if sent.text.strip()
#                 ]

#                 for ref in refs:
#                     target_attr = ref.attrib.get("target", "")
#                     if not target_attr:
#                         continue
#                     target_ids = [t.strip().lstrip("#") for t in target_attr.split()]
#                     ref_text = "".join(ref.itertext()).strip()

#                     for tid in target_ids:
#                         if tid in bibl_id_to_urls:
#                             for url in bibl_id_to_urls[tid]:
#                                 url_to_paragraphs.setdefault(url, []).append(paragraph_text)
#                                 if section_title:
#                                     url_to_titles.setdefault(url, []).append(section_title)

#                                 matched = False
#                                 for s in sentence_texts:
#                                     if ref_text and ref_text in s:
#                                         url_to_sentences.setdefault(url, []).append(s)
#                                         matched = True
#                                         break
#                                 if matched:
#                                     continue

#                                 norm_ref = re.sub(r'[^A-Za-z0-9]', '', ref_text).lower()
#                                 if norm_ref:
#                                     for sp in sentence_spans:
#                                         norm_sent = re.sub(r'[^A-Za-z0-9]', '', sp["text"]).lower()
#                                         if norm_ref in norm_sent:
#                                             url_to_sentences.setdefault(url, []).append(sp["text"])
#                                             matched = True
#                                             break
#                                 if matched:
#                                     continue

#                                 try:
#                                     idx = paragraph_text.index(ref_text)
#                                 except ValueError:
#                                     idx = -1
#                                 if idx != -1:
#                                     for sp in sentence_spans:
#                                         if sp["start"] <= idx < sp["end"]:
#                                             url_to_sentences.setdefault(url, []).append(sp["text"])
#                                             matched = True
#                                             break

#             # === Citation 情報をまとめる（同じ） ===
#             for bibl in bibl_structs:
#                 urls = bibl.findall(".//tei:ptr[@target]", namespaces=ns)
#                 for url_elem in urls:
#                     url = url_elem.attrib.get("target", "").strip()
#                     if not url:
#                         continue

#                     paragraphs_with_ref = url_to_paragraphs.get(url, [])
#                     sentences_with_ref = url_to_sentences.get(url, [])
#                     titles_with_ref = url_to_titles.get(url, [])

#                     bibl_id = bibl.attrib.get("{http://www.w3.org/XML/1998/namespace}id", "")
#                     citation_text = bibl_id_to_text.get(bibl_id, "")
#                     citation_info_combined = f"{citation_text} {url}" if citation_text else url

#                     for i, (para_text, title_text, sent_text) in enumerate(zip_longest(
#                         paragraphs_with_ref,
#                         titles_with_ref,
#                         sentences_with_ref,
#                         fillvalue=""
#                     )):
#                         citation_paragraph_text = para_text
#                         citation_sentence_text = sent_text
#                         paragraph_titles_text = title_text if isinstance(title_text, list) else []

#                         if not citation_paragraph_text:
#                             no_para_count += 1
#                         else:
#                             para_count += 1
#                             if not citation_sentence_text:
#                                 para_no_sen_count += 1
#                         if not citation_sentence_text:
#                             no_sen_count += 1
#                         else:
#                             sen_count += 1

#                         ref_records.append({
#                             "Citation-type": "Reference",
#                             "Citation-info": citation_info_combined,
#                             "Paragraph-title": paragraph_titles_text,
#                             "Citation-sentence": citation_sentence_text,
#                             "Citation-paragraph": citation_paragraph_text,
#                             "URL": url
#                         })

#             paper_title = file.replace(".xml", "")
#             if ref_records:
#                 xml_ref_dict[paper_title] = ref_records

#     return xml_ref_dict

# GROBID XML（TEI形式）から参考文献URLを抽出する関数
def extract_references_from_xml(xml_folder):
    global para_count, no_para_count, sen_count, no_sen_count, para_no_sen_count, url_count, url_set_count

    xml_ref_dict = {}

    for parent, dirs, files in os.walk(xml_folder):
        for file in files:
            if not file.endswith(".xml"):
                continue
            file_path = os.path.join(parent, file)

            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
            except Exception as e:
                print(f"XML parse error in {file}: {e}")
                continue

            ns = {"tei": "http://www.tei-c.org/ns/1.0"}

            # === 参考文献リストを取得 ===
            bibl_structs = root.findall(".//tei:listBibl/tei:biblStruct", ns)
            ref_records = []
            all_urls = []

            bibl_id_to_urls = {}
            # --- 変更点: 書誌情報テキストも同時に取得して保存する ---
            bibl_id_to_text = {}

            for bibl in bibl_structs:
                bibl_id = bibl.attrib.get("{http://www.w3.org/XML/1998/namespace}id", "")

                # 書誌情報（できるだけ生テキストで）
                # biblStruct全体のテキストを抽出（著者名・タイトルなど含む）
                # bibl_text = " ".join(" ".join(bibl.itertext()).split())
                bibl_text = extract_bibl_info_as_dict(bibl, ns)       # Citation-infoを詳しくする
                if bibl_text:
                    bibl_id_to_text[bibl_id] = bibl_text

                # URL抽出
                urls = bibl.findall(".//tei:ptr[@target]", ns)
                for url_elem in urls:
                    url = url_elem.attrib.get("target", "").strip()
                    if not url.startswith(("http", "https", "ftp")):
                        continue
                    all_urls.append(url)
                    if not url:
                        continue
                    if bibl_id:
                        bibl_id_to_urls.setdefault(bibl_id, []).append(url)
            url_count += len(all_urls)
            url_set_count += len(set(all_urls))

            # --- 段落探索（本文） ---
            paragraphs = root.findall(".//tei:text//tei:body//tei:p", ns)
            # if not paragraphs:
            #     paragraphs = root.findall(".//tei:text//tei:body//tei:div//tei:p", ns)

            # --- parent_map作成 ---
            parent_map = {}
            for par in root.iter():
                for child in par:
                    parent_map[child] = par

            url_to_paragraphs = {}
            url_to_sentences = {}
            url_to_titles = {}
            url_to_sentences_raw = {}

            for p in paragraphs:
                paragraph_parts = []
                for elem in p.iter():
                    if elem.tag == f"{{{ns['tei']}}}ref" and elem.attrib.get("type") == "bibr":
                        ref_text = "".join(elem.itertext()).strip()
                        paragraph_parts.append(ref_text)
                    elif elem.text and elem.tag != f"{{{ns['tei']}}}ref":
                        paragraph_parts.append(elem.text)
                    if elem.tail:
                        paragraph_parts.append(elem.tail)

                paragraph_text = "".join(paragraph_parts).replace("\n", " ").replace("\t", " ").strip()
                if not paragraph_text:
                    continue

                refs = p.findall(".//tei:ref[@type='bibr']", ns)
                if not refs:
                    continue

                # --- セクションタイトル探索 ---
                section_titles = []
                ancestor = p
                seen = set()
                current_head = None

                while ancestor is not None:
                    head = ancestor.find("./tei:head[@n]", ns)
                    if head is None:
                        head = ancestor.find("./tei:head", ns)
                    if head is not None:
                        current_head = head
                        break
                    ancestor = parent_map.get(ancestor)

                if current_head is not None:
                    n_value = current_head.attrib.get("n", "").strip()
                    head_text = "".join(current_head.itertext()).strip()

                    if n_value:
                        section_titles.append(f"{n_value} {head_text}")
                        seen.add(n_value)
                    elif head_text:
                        section_titles.append(head_text)
                        seen.add(head_text)
                    if n_value:
                        parts = n_value.split(".")
                        while len(parts) > 1:
                            parts = parts[:-1]
                            parent_n = ".".join(parts)
                            parent_head = root.find(f".//tei:head[@n='{parent_n}']", ns)
                            if parent_head is not None:
                                parent_text = "".join(parent_head.itertext()).strip()
                                full_title = f"{parent_n} {parent_text}"
                                if full_title not in seen:
                                    section_titles.insert(0, full_title)
                                    seen.add(full_title)

                section_title = section_titles
                # print(section_title)
                # --- 文分割 ---
                doc = nlp(paragraph_text)
                sentence_texts = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
                sentence_spans = [
                    {"start": sent.start_char, "end": sent.end_char, "text": sent.text.strip()}
                    for sent in doc.sents if sent.text.strip()
                ]

                for ref in refs:
                    target_attr = ref.attrib.get("target", "")
                    if not target_attr:
                        continue
                    target_ids = [t.strip().lstrip("#") for t in target_attr.split()]
                    ref_text = "".join(ref.itertext()).strip()
                    # print(ref_text)
                    for tid in target_ids:
                        if tid in bibl_id_to_urls:
                            for url in bibl_id_to_urls[tid]:
                            #     url_to_paragraphs.setdefault(url, []).append(paragraph_text)
                            #     if section_title:
                            #         url_to_titles.setdefault(url, []).append(section_title)
                                url_to_sentences.setdefault(url, [])
                                url_to_sentences_raw.setdefault(url, [])
                                url_to_paragraphs.setdefault(url, [])
                                url_to_titles.setdefault(url, [])
                                matched = False
                                for s in sentence_texts:
                                    if ref_text and ref_text in s:
                                        if s not in url_to_sentences_raw[url]:  
                                            if f"{ref_text}[Cite_Ref]" not in paragraph_text:
                                                new_paragraph_text = paragraph_text.replace(ref_text, ref_text + "[Cite_Ref]")
                                            else:
                                                new_paragraph_text = paragraph_text

                                            if f"{ref_text}[Cite_Ref]" not in s:
                                                new_s = s.replace(ref_text, ref_text + "[Cite_Ref]")
                                            else:
                                                new_s = s                                                                                      
                                            url_to_paragraphs[url].append(new_paragraph_text)
                                            if section_title:
                                                url_to_titles[url].append(section_title)
                                            url_to_sentences[url].append(new_s)
                                            url_to_sentences_raw[url].append(s)
                                        matched = True
                                        # break
                                # if matched:
                                #     continue

                                # for m in re.finditer(re.escape(ref_text), paragraph_text):
                                #     idx = m.start()
                                #     for sp in sentence_spans:
                                #         if sp["start"] <= idx < sp["end"]:
                                #             s_raw = sp["text"]
                                #             if s_raw not in url_to_sentences_raw[url]:
                                #                 if f"{ref_text}[Cite_Ref]" not in paragraph_text:
                                #                     new_paragraph_text = paragraph_text.replace(ref_text, ref_text + "[Cite_Ref]")
                                #                 else:
                                #                     new_paragraph_text = paragraph_text

                                #                 if f"{ref_text}[Cite_Ref]" not in s:
                                #                     print(f"=====位置ベースで登録 {ref_text}=====")
                                #                     new_s = s_raw.replace(ref_text, ref_text + "[Cite_Ref]")
                                #                 else:
                                #                     new_s = s_raw                                                
                                #                 url_to_paragraphs[url].append(new_paragraph_text)
                                #                 if section_title:
                                #                     url_to_titles.setdefault(url, []).append(section_title)
                                #                 url_to_sentences[url].append(new_s)
                                #                 url_to_sentences_raw[url].append(s_raw)
                                #             matched = True
                                            # break
                                # if matched:
                                #     continue
                                # norm_ref = re.sub(r'[^A-Za-z0-9]', '', ref_text).lower()
                                
                                # if norm_ref:
                                #     for sp in sentence_spans:
                                #         norm_sent = re.sub(r'[^A-Za-z0-9]', '', sp["text"]).lower()
                                #         if norm_ref in norm_sent:
                                #             if sp["text"] not in url_to_sentences.setdefault(url, []):
                                #                 url_to_paragraphs.setdefault(url, []).append(paragraph_text)
                                #                 if section_title:
                                #                     url_to_titles.setdefault(url, []).append(section_title)
                                #                 url_to_sentences[url].append(sp["text"])
                                #             matched = True
                                #             # break

            # === Citation 情報をまとめる ===
            for bibl in bibl_structs:
                urls = bibl.findall(".//tei:ptr[@target]", ns)
                for url_elem in urls:
                    url = url_elem.attrib.get("target", "").strip()
                    if not url:
                        continue

                    paragraphs_with_ref = url_to_paragraphs.get(url, [])
                    sentences_with_ref = url_to_sentences.get(url, [])
                    titles_with_ref = url_to_titles.get(url, [])

                    # --- 変更点: 書誌情報を取得（bibl_idに対応） ---
                    bibl_id = bibl.attrib.get("{http://www.w3.org/XML/1998/namespace}id", "")
                    citation_text = bibl_id_to_text.get(bibl_id, "")
                    citation_info_combined = f"{citation_text}" if citation_text else url

                    for i, (para_text, title_text, sent_text) in enumerate(zip_longest(
                        paragraphs_with_ref,
                        titles_with_ref,
                        sentences_with_ref,
                        fillvalue=""
                    )):
                        citation_paragraph_text = para_text
                        citation_sentence_text = sent_text
                        paragraph_titles_text = title_text if isinstance(title_text, list) else []

                        if not citation_paragraph_text:
                            no_para_count += 1
                        else:
                            para_count += 1
                            if not citation_sentence_text:
                                para_no_sen_count += 1
                        if not citation_sentence_text:
                            no_sen_count += 1
                        else:
                            sen_count += 1

                        ref_records.append({
                            "Citation-type": "Reference",
                            "Citation-info": citation_info_combined,  # --- 変更点: 書誌情報 + URL ---
                            "Paragraph-title": paragraph_titles_text,
                            "Citation-sentence": citation_sentence_text,
                            "Citation-paragraph": citation_paragraph_text,
                            "URL":url
                        })

            paper_title = file.replace(".xml", "")
            if ref_records:
                xml_ref_dict[paper_title] = ref_records

    return xml_ref_dict


# === 実行部 ===
if os.getenv("DATASET_PARSER_CPU") != "1":
    spacy.require_gpu()
nlp = spacy.load('en_core_web_trf')

no_para_count = 0
para_count = 0
sen_count = 0
no_sen_count = 0
para_no_sen_count = 0
url_count = 0
url_set_count = 0
xml_folder = "data/xml"
xml_reference_dict = extract_references_from_xml(xml_folder)
# xml_reference_dict = extract_references_from_xml_lxml(xml_folder)     # lxmlを用いる
with open("data/intermediate/xml_ref_dict.json", "w", encoding="utf-8") as f:
    json.dump(xml_reference_dict, f, ensure_ascii=False, indent=2) 

# print(xml_reference_dict)
print("参考文献にURLを含む論文数：", len(xml_reference_dict))
print("引用段落文が取得できない数：", no_para_count)
print("引用段落文が取得できた数：", para_count)
print("引用文を取得できた数：", sen_count)
print("引用文を取得できない数：", no_sen_count)
print("引用段落文は取得できるが引用文は取得できない数：", para_no_sen_count)
print("参考文献のURLの数", url_count)
print("ユニークなURLの数：", url_set_count)
print(spacy.__version__)
print(nlp.meta["version"])
