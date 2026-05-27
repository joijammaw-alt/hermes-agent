import os
import sys
import re
import requests
from dotenv import load_dotenv

# ป้องกัน UnicodeEncodeError เมื่อพิมพ์ข้อความภาษาไทยหรือ Emoji บน Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# โหลด Environment Variables
load_dotenv()

wp_url = os.getenv("WP_URL")
wp_user = os.getenv("WP_USER")
wp_pass = os.getenv("WP_PASS")

if not wp_url or not wp_user or not wp_pass:
    print("❌ ERROR: กรุณากำหนดค่า WP_URL, WP_USER, และ WP_PASS ในไฟล์ .env")
    exit(1)

api_url = wp_url.rstrip("/") + "/wp-json/wp/v2/posts"

def get_project_paths():
    """หาโฟลเดอร์หลักและเก็บพาธที่ถูกต้อง"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == "tools":
        project_root = os.path.dirname(current_dir)
    else:
        project_root = current_dir
    
    vault_dir = os.path.join(project_root, "Obsidian_Vault")
    history_file = os.path.join(project_root, "history.txt")
    
    return project_root, vault_dir, history_file

def load_history(history_path):
    """โหลดประวัติการโพสต์สำเร็จมาจาก history.txt"""
    if not os.path.exists(history_path):
        return set()
    with open(history_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_to_history(history_path, filename):
    """บันทึกชื่อไฟล์ที่โพสต์สำเร็จลงใน history.txt"""
    with open(history_path, 'a', encoding='utf-8') as f:
        f.write(filename + '\n')

def get_blog_files(vault_dir):
    """หาไฟล์ blog_post_*.md ทั้งหมดใน Obsidian_Vault ตั้งแต่หมายเลข 2 เป็นต้นไป"""
    if not os.path.exists(vault_dir):
        print(f"❌ ERROR: ไม่พบโฟลเดอร์ Obsidian_Vault ที่ {vault_dir}")
        return []
        
    files = []
    for f in os.listdir(vault_dir):
        if f.startswith("blog_post_") and f.endswith(".md"):
            match = re.search(r'blog_post_(\d+)\.md', f)
            if match:
                num = int(match.group(1))
                if num >= 2: # ข้าม blog_post_1.md และดึงตั้งแต่ blog_post_2.md ขึ้นไป
                    files.append((num, f))
    
    # เรียงลำดับตามตัวเลขในชื่อไฟล์จากน้อยไปหามาก
    files.sort()
    return [item[1] for item in files]

def parse_markdown_file(file_path):
    """อ่านและแยกแยะ Frontmatter กับเนื้อหาหลักของไฟล์ Markdown พร้อมแปลงเป็น HTML อย่างง่าย"""
    if not os.path.exists(file_path):
        print(f"⚠️ Warning: ไม่พบไฟล์ {file_path}")
        return None, None

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # แยก Frontmatter
    parts = content.split('---')
    if len(parts) < 3:
        title = os.path.basename(file_path).replace('.md', '')
        body = content
    else:
        frontmatter = parts[1]
        body = '---'.join(parts[2:])

        title_match = re.search(r'title:\s*["\']?(.*?)["\']?\s*\n', frontmatter)
        if title_match:
            title = title_match.group(1)
        else:
            title = os.path.basename(file_path).replace('.md', '')

    # แปลง Markdown Body เป็น HTML อย่างง่าย
    html_lines = []
    in_list = False

    for line in body.split('\n'):
        line_str = line.strip()
        if not line_str:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue

        if line_str.startswith('# '):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{line_str[2:]}</h2>")
        elif line_str.startswith('## '):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{line_str[3:]}</h3>")
        elif line_str.startswith('### '):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h4>{line_str[4:]}</h4>")
        elif line_str.startswith('- ') or line_str.startswith('* '):
            if not in_list:
                html_lines.append("<ul class='wp-block-list'>")
                in_list = True
            html_lines.append(f"<li>{line_str[2:]}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{line_str}</p>")

    if in_list:
        html_lines.append("</ul>")

    html_content = "\n".join(html_lines)
    return title, html_content

def post_to_wordpress(title, html_content):
    """ส่งบทความไปยัง WordPress REST API"""
    payload = {
        "title": title,
        "content": html_content,
        "status": "publish"
    }

    try:
        res = requests.post(api_url, json=payload, auth=(wp_user, wp_pass), timeout=15)
        if res.status_code == 201:
            data = res.json()
            return True, data.get("id"), data.get("link")
        else:
            return False, res.status_code, res.text
    except Exception as e:
        return False, "CONNECTION_ERROR", str(e)

def main():
    project_root, vault_dir, history_path = get_project_paths()
    
    print("=" * 60)
    print("🚀 เริ่มต้นระบบการโพสต์บทความอัตโนมัติไปยัง WordPress")
    print(f"📍 WordPress URL: {wp_url}")
    print(f"👤 บัญชีผู้ใช้: {wp_user}")
    print(f"📜 ไฟล์ประวัติการโพสต์: {os.path.basename(history_path)}")
    print("=" * 60)

    # โหลดประวัติการโพสต์เดิม
    history = load_history(history_path)
    
    # ค้นหาไฟล์ blog_post_*.md ที่จะโพสต์ทั้งหมด
    blog_files = get_blog_files(vault_dir)
    
    if not blog_files:
        print("❌ ไม่พบไฟล์บทความที่จะทำการโพสต์ใน Obsidian_Vault")
        return

    total_files = len(blog_files)
    print(f"📂 ค้นพบไฟล์บทความที่เข้าเกณฑ์ทั้งหมด {total_files} ไฟล์")

    for idx, file_name in enumerate(blog_files, 1):
        print(f"\n📂 ขั้นตอนที่ {idx}/{total_files}: ตรวจสอบไฟล์ '{file_name}'...")
        
        # 1. ตรวจสอบประวัติการโพสต์ซ้ำจาก history.txt
        if file_name in history:
            print(f"⏭️  File already posted, skipping. (ข้าม '{file_name}' เนื่องจากเคยโพสต์สำเร็จไปแล้ว)")
            continue
            
        file_path = os.path.join(vault_dir, file_name)
        title, html_content = parse_markdown_file(file_path)
        if not title:
            print(f"❌ ข้ามเนื่องจากโครงสร้างไฟล์ {file_name} ไม่ถูกต้อง")
            continue

        print(f"📝 หัวข้อข่าว: '{title}'")
        print(f"🤖 กำลังเผยแพร่ข่าวขึ้น WordPress...")

        # 2. ส่งบทความไป WordPress
        success, info_or_code, link_or_msg = post_to_wordpress(title, html_content)
        
        if success:
            print(f"✅ โพสต์สำเร็จ! [Post ID: {info_or_code}]")
            print(f"🔗 ลิงก์บทความ: {link_or_msg}")
            # 3. บันทึกผลลัพธ์ลงประวัติเพื่อป้องกันการส่งซ้ำในอนาคต
            save_to_history(history_path, file_name)
            print(f"💾 บันทึก '{file_name}' ลงประวัติเรียบร้อย")
        else:
            print(f"❌ โพสต์ล้มเหลว! [Error Code: {info_or_code}]")
            print(f"📄 รายละเอียด: {link_or_msg}")

    print("\n" + "=" * 60)
    print("🎉 สิ้นสุดกระบวนการตรวจสอบและโพสต์บทความเสร็จสมบูรณ์!")
    print("=" * 60)

if __name__ == "__main__":
    main()
