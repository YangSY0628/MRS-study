import hashlib
import os
import time
import re
import requests

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
    links = re.findall(r'\[(.*?)\]\((http[s]?://.*?)\)', content)
    return links

# 获取论文信息
def fetch_paper_info(url):
    response = requests.get(f"{SEMANTIC_SCHOLAR_API}/{url}")
    if response.status_code == 200:
        data = response.json()
        title = data.get("title", "Unknown Title")
        citation_count = data.get("citationCount", 0)
        year = data.get("year", "Unknown Year")
        return title, year, citation_count
    else:
        return None, None, None

# 更新Markdown内容
def update_markdown_with_paper_info(content, links):
    for link_text, link_url in links:
        print(f"Processing: {link_url}")
        title, year, citation_count = fetch_paper_info(link_url)
        if title and year and citation_count is not None:
            updated_info = f"{link_text} (Published: {year}, Citations: {citation_count})"
            content = content.replace(f"[{link_text}]({link_url})", f"[{updated_info}]({link_url})")
    return content

# 写回Markdown文件
def write_updated_markdown(file_path, updated_content):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

# 检测文件是否包含论文链接
def contains_paper_links(content):
    links = extract_links_from_markdown(content)
    # 检测是否有 DOI 或其他论文链接格式
    paper_links = [link for _, link in links if "doi.org" in link or "semanticscholar.org" in link]
    return bool(paper_links), paper_links

# 主程序
def monitor_and_process_markdown(file_path, interval=5):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return

    # 初始哈希值
    last_hash = calculate_file_hash(file_path)
    print("Monitoring for changes...")

    while True:
        time.sleep(interval)  # 等待一段时间再检查
        current_hash = calculate_file_hash(file_path)
        if current_hash != last_hash:  # 如果文件发生改动
            print("File changed. Checking for paper links...")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            has_links, paper_links = contains_paper_links(content)
            if has_links:  # 如果包含论文链接
                print("Paper links detected. Processing...")
                updated_content = update_markdown_with_paper_info(content, paper_links)
                write_updated_markdown(file_path, updated_content)
                print("Markdown file updated with paper information.")
            else:
                print("No paper links detected in the changes.")
            
            # 更新哈希值
            last_hash = current_hash
        else:
            print("No changes detected.")

if __name__ == "__main__":
    markdown_file = "your_markdown_file.md"  # 替换为你的Markdown文件路径
    monitor_and_process_markdown(markdown_file)