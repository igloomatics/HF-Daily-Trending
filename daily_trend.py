import os
PROXY_PORT = "7890" 

os.environ["http_proxy"] = f"http://127.0.0.1:{PROXY_PORT}"
os.environ["https_proxy"] = f"http://127.0.0.1:{PROXY_PORT}"
import datetime
import requests
from huggingface_hub import HfApi

# ==========================================
#  Hugging Face 官方版本 (无需镜像，需外网)
# ==========================================

# 1. 初始化 API (不传 endpoint 参数，默认连接官方)
api = HfApi()

def get_trending_models(limit=5):
    print("正在抓取热门模型 (Trending Models)...")
    # 获取最近更新的模型
    recent_models = api.list_models(
        sort="lastModified", 
        direction=-1, 
        limit=100, 
        full=False
    )
    # 按点赞数排序
    sorted_models = sorted(
        recent_models, 
        key=lambda x: getattr(x, 'likes', 0), 
        reverse=True
    )
    return sorted_models[:limit]


def get_trending_datasets(limit=5):
    print("正在抓取热门数据集 (Trending Datasets)...")
    recent_datasets = api.list_datasets(
        sort="lastModified",
        direction=-1,
        limit=100,
        full=False
    )
    sorted_datasets = sorted(
        recent_datasets, 
        key=lambda x: getattr(x, 'likes', 0), 
        reverse=True
    )
    return sorted_datasets[:limit]

def get_trending_spaces(limit=5):
    print("正在抓取热门应用 (Trending Spaces)...")
    recent_spaces = api.list_spaces(
        sort="lastModified",
        direction=-1,
        limit=100,
        full=False
    )
    sorted_spaces = sorted(
        recent_spaces, 
        key=lambda x: getattr(x, 'likes', 0), 
        reverse=True
    )
    return sorted_spaces[:limit]



def get_trending_papers(limit=5):
    print("-" * 30)
    print("🚀 开始抓取 HF Daily Papers (仅今日版)...")
    
    # --- 修改点：只获取今天，去掉昨天 ---
    today = datetime.datetime.now(datetime.timezone.utc).date()
    target_dates = [today] # 列表里只有今天
    
    papers_map = {}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for date_obj in target_dates:
        date_str = date_obj.strftime('%Y-%m-%d')
        url = f"https://huggingface.co/api/daily_papers?date={date_str}"
        print(f"   📅 扫描日期: {date_str} ...")
        
        try:
            response = requests.get(url, headers=headers, timeout=20, verify=False)
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ 发现 {len(data)} 篇候选")
                
                for item in data:
                    paper_info = item.get('paper', {})
                    p_id = paper_info.get('id')
                    title = item.get('title') or paper_info.get('title')
                    
                    if not p_id: continue

                    # 1. 获取点赞数
                    raw_upvotes = (
                        paper_info.get('numUpvotes') or 
                        paper_info.get('upvotes') or 
                        item.get('numUpvotes') or 
                        0
                    )
                    current_upvotes = int(raw_upvotes)

                    # 2. 三层机构查找逻辑 (保持不变)
                    target_org = None
                    orgs_list = paper_info.get('organizations')
                    if orgs_list and isinstance(orgs_list, list) and len(orgs_list) > 0:
                        target_org = orgs_list[0]
                    if not target_org:
                        target_org = paper_info.get('organization')
                    if not target_org:
                        target_org = item.get('organization')

                    # 3. 提取信息
                    if target_org:
                        inst_name = target_org.get('fullname') or target_org.get('name')
                        inst_username = target_org.get('name')
                        inst_emoji = "🏢"
                    else:
                        submitter = item.get('submittedBy', {})
                        inst_name = submitter.get('fullname') or submitter.get('name') or "Unknown"
                        inst_username = submitter.get('name')
                        inst_emoji = "👤"
                    
                    if inst_username:
                        inst_url = f"https://huggingface.co/{inst_username}"
                    else:
                        inst_url = "#"

                    # 4. 存入字典 (因为只有一天，其实不用比大小了，但为了逻辑统一保留)
                    papers_map[p_id] = {
                        'title': title,
                        'id': p_id,
                        'upvotes': current_upvotes,
                        'url': f"https://huggingface.co/papers/{p_id}",
                        'inst_name': inst_name,
                        'inst_url': inst_url,
                        'inst_emoji': inst_emoji
                    }
            else:
                print(f"      ⚠️ 状态码: {response.status_code}")
        except Exception as e:
            print(f"      ❌ 请求错误: {e}")

    # 排序与截取
    all_candidates = list(papers_map.values())
    all_candidates.sort(key=lambda x: x['upvotes'], reverse=True)
    top_papers = all_candidates[:limit]
    
    print(f"🔥 最终 Top {limit}:")
    for p in top_papers:
        print(f"   👍 {p['upvotes']} | {p['inst_emoji']} {p['inst_name']} | {p['title'][:20]}...")
    print("-" * 30)

    return top_papers

def format_model_list(items):
    if not items: return "暂无数据"
    lines = []
    for item in items:
        # 官方链接
        url = f"https://huggingface.co/{item.id}"
        likes = getattr(item, 'likes', 0)
        downloads = getattr(item, 'downloads', 0)
        line = f"- {item.id} [🔗]({url}) (🌟 {likes} | 📥 {downloads})"
        lines.append(line)
    return "\n".join(lines)

def format_dataset_list(items):
    if not items: return "暂无数据"
    lines = []
    for item in items:
        # 官方链接 /datasets/
        url = f"https://huggingface.co/datasets/{item.id}"
        likes = getattr(item, 'likes', 0)
        downloads = getattr(item, 'downloads', 0)
        line = f"- {item.id} [🔗]({url}) (🌟 {likes} | 📥 {downloads})"
        lines.append(line)
    return "\n".join(lines)

def format_space_list(items):
    if not items: return "暂无数据"
    lines = []
    for item in items:
        # 官方链接 /spaces/
        url = f"https://huggingface.co/spaces/{item.id}"
        likes = getattr(item, 'likes', 0)
        line = f"- {item.id} [🔗]({url}) (🌟 {likes})"
        lines.append(line)
    return "\n".join(lines)

def format_paper_list(items):
    if not items: 
        return "暂无数据"
    
    lines = []
    for item in items:
        # 提取数据
        title = item.get('title', 'Unknown')
        paper_url = item.get('url', '#')
        upvotes = item.get('upvotes', 0)
        
        # 提取机构信息
        inst_name = item.get('inst_name', 'Unknown')
        inst_url = item.get('inst_url', '#')
        inst_emoji = item.get('inst_emoji', '🏢') # 默认为机构图标

        # 标题去换行
        display_title = title.replace("\n", " ").strip()
        
        # --- 排版生成 ---
        # 第一行：**标题**
        # 第二行：(缩进) 图标 [机构名](链接) • 👍 点赞 • [View Paper](链接)
        line = (
            f"- **{display_title}**\n"
            f"  {inst_emoji} [{inst_name}]({inst_url}) • 👍 {upvotes} • [View Paper]({paper_url})"
        )
        lines.append(line)
        
    return "\n".join(lines)


def generate_report():
    # 1. 获取数据
    models = get_trending_models(5)
    datasets = get_trending_datasets(5)
    spaces = get_trending_spaces(5)
    papers = get_trending_papers(5)
    
    # 2. 生成 Markdown 文本
    report = f"""# Hugging Face Daily Trending (Official)
Update Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### ℹ️ About this Report
This report is automatically generated daily using the Hugging Face API.
* **Models, Datasets & Spaces**: We fetch the **100 most recently updated** items and sort them by **Likes (🌟)** to identify trending high-quality content.
* **Papers**: We fetch the official **Daily Papers** from Hugging Face and sort them by **Upvotes (👍)**.


## 🧠 Trending Models
{format_model_list(models)}

## ⛽ Trending Datasets
{format_dataset_list(datasets)}

## 🏠 Trending Spaces
{format_space_list(spaces)}

## 📄 Trending Papers
{format_paper_list(papers)}
"""
    return report


if __name__ == "__main__":
    try:
        report = generate_report()
        
        print("\n" + "="*30)
        print(report)
        print("="*30 + "\n")
        
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("✅ Report generated and saved to README.md")
        
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        print("请确保你能够直接访问 https://huggingface.co")