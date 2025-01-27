import hashlib
import os
import time
import re
import requests
import xml.etree.ElementTree as ET
import difflib

# Semantic Scholar API URL
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/v1/paper"

# 获取文件的哈希值，用于检测改动
def calculate_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

# 提取Markdown文件中的链接
def extract_links_from_markdown(content):
    links = re.findall(r'(http[s]?://[^\s]+)', content)
    return links

def fetch_paper_info(url):
    # 确保传递给 API 的 URL 是完整的
    response = requests.get(f"{SEMANTIC_SCHOLAR_API}?url={url}")
    if response.status_code == 200:
        data = response.json()
        title = data.get("title", "Unknown Title")
        citation_count = data.get("citationCount", 0)
        year = data.get("year", "Unknown Year")
        return title, year, citation_count
    else:
        return None, None, None

def fetch_paper_info_from_arxiv(url):
    arxiv_id = url.split('/')[-1]
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        published = entry.find('{http://www.w3.org/2005/Atom}published').text
        year = published.split('-')[0]
        citation_count = 0  # arXiv does not provide citation count
        return title, year, citation_count
    else:
        return None, None, None
    
# 更新Markdown内容
def update_markdown_with_paper_info(content, links):
    updated_content = content
    for link_url in links:
        print(f"Processing: {link_url}")
        title, year, citation_count = fetch_paper_info_from_arxiv(link_url)
        if title and year and citation_count is not None:
            updated_info = f"(Title: {title}, Published: {year}, Citations: {citation_count})"
            updated_content = updated_info
    return updated_content

# 写回Markdown文件
def write_updated_markdown(file_path, updated_content):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(updated_content)

# 检测文件是否包含论文链接
def contains_paper_links(content):
    links = extract_links_from_markdown(content)
    print(f"links are {links}")
    # 检测是否有 DOI、arXiv 或其他论文链接格式
    paper_links = [link for link in links if "doi.org" in link or "semanticscholar.org" in link or "arxiv.org" in link]
    return bool(paper_links), paper_links

def get_diff(content1, content2):
    diff = difflib.unified_diff(content1.splitlines(), content2.splitlines(), lineterm='')
    useful_diff = []
    for line in diff:
        if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
            continue
        useful_diff.append(line)
    return useful_diff[-1] if useful_diff else ''

def get_file_content(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# 主程序
def monitor_and_process_markdown(file_path, interval=5):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return

    # 初始内容
    last_content = get_file_content(file_path)
    print("Monitoring for changes...")

    while True:
        time.sleep(interval)  # 等待一段时间再检查
        current_content = get_file_content(file_path)
        if current_content != last_content:  # 如果文件内容发生改动
            print("File content changed. Checking for paper links...")
            diff = get_diff(last_content, current_content)
            print(f"Diff: {diff}")
            has_links, paper_links = contains_paper_links(diff)
            if has_links:  # 如果包含论文链接
                print("Paper links detected in changes. Processing...")
                new_content = update_markdown_with_paper_info(diff, paper_links)
                write_updated_markdown(file_path, new_content)
                updated_content = get_file_content(file_path)
                print("Markdown file updated with paper information.")
                last_content = updated_content  # 更新最后的内容
            else:
                print("No paper links detected in the changes.")
                last_content = current_content  # 更新最后的内容
        else:
            print("No changes detected.")

if __name__ == "__main__":
    markdown_file = "test.md"  # 替换为你的Markdown文件路径
    monitor_and_process_markdown(markdown_file)