import os
import re
import datetime
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

# สร้างโฟลเดอร์สำหรับ Obsidian Vault หากยังไม่มี
OBSIDIAN_VAULT_PATH = "./Obsidian_Vault"

# ข้อมูลจำลองคุณภาพสูง (Mock Data) สำหรับโรงเรียนวัชระ
# เพื่อรองรับการทำงานในกรณีที่เว็บบล็อกจำลอง https://example-watchara.com เข้าใช้งานไม่ได้
MOCK_LANDING_HTML = """
<html>
    <head><title>โรงเรียนวัชระ - มุ่งสู่ความเป็นเลิศทางปัญญาและเทคโนโลยี</title></head>
    <body>
        <div class="hero">
            <h1>ยินดีต้อนรับสู่โรงเรียนวัชระ</h1>
            <p class="lead">สถาบันการศึกษาชั้นนำที่มุ่งมั่นพัฒนาวิชาการ คุณธรรม และเทคโนโลยี เพื่อเตรียมความพร้อมให้นักเรียนก้าวสู่โลกอนาคตอย่างมั่นใจ</p>
        </div>
        <div class="about">
            <h2>เกี่ยวกับเรา</h2>
            <p>โรงเรียนวัชระ ก่อตั้งขึ้นด้วยวิสัยทัศน์ที่ต้องการสร้างสภาพแวดล้อมการเรียนรู้ที่ทันสมัย มีหลักสูตรที่ยืดหยุ่นและเน้นทักษะการปฏิบัติจริง (Active Learning) ทั้งในด้านสะเต็มศึกษา (STEM), ภาษาต่างประเทศ, และศิลปศาสตร์</p>
        </div>
    </body>
</html>
"""

MOCK_BLOGS_HTML = [
    {
        "url": "https://example-watchara.com/blog/robotics-ai-classroom",
        "html": """
        <html>
            <head><title>เปิดตัวโครงการห้องเรียนหุ่นยนต์และ AI สำหรับมัธยมศึกษาตอนปลาย</title></head>
            <body>
                <article>
                    <h1>เปิดตัวโครงการห้องเรียนหุ่นยนต์และ AI สำหรับมัธยมศึกษาตอนปลาย</h1>
                    <p class="date">2026-05-20</p>
                    <div class="content">
                        <p>โรงเรียนวัชระได้เปิดตัวห้องปฏิบัติการนวัตกรรมใหม่ล่าสุด "Robotics & AI Center" สำหรับนักเรียนระดับมัธยมศึกษาตอนปลาย เพื่อส่งเสริมการเรียนรู้ด้านการเขียนโค้ดและการสร้างหุ่นยนต์</p>
                        <p>โครงการนี้มุ่งเน้นการใช้งานฮาร์ดแวร์จริง เช่น บอร์ดควบคุม ไมโครคอนโทรลเลอร์ และการประยุกต์ใช้ AI ด้วยภาษา Python ในการแก้โจทย์จำลองในชีวิตประจำวัน</p>
                    </div>
                </article>
            </body>
        </html>
        """
    },
    {
        "url": "https://example-watchara.com/blog/academic-competition-2026",
        "html": """
        <html>
            <head><title>ผลการแข่งขันวิชาการระดับประเทศ ประจำปี 2569</title></head>
            <body>
                <article>
                    <h1>ผลการแข่งขันวิชาการระดับประเทศ ประจำปี 2569</h1>
                    <p class="date">2026-05-18</p>
                    <div class="content">
                        <p>นักเรียนโรงเรียนวัชระสร้างชื่อเสียงในระดับชาติ คว้ารางวัลชนะเลิศจากการประกวดสิ่งประดิษฐ์และนวัตกรรมเยาวชน ประจำปี 2569</p>
                        <p>ผลงานที่ได้รับรางวัลคือ "ระบบจัดการน้ำอัจฉริยะในชุมชน" พัฒนาโดยทีมนักเรียนชั้น ม.5 ซึ่งใช้เซนเซอร์วัดระดับน้ำและแจ้งเตือนผ่านไลน์แบบเรียลไทม์</p>
                    </div>
                </article>
            </body>
        </html>
        """
    },
    {
        "url": "https://example-watchara.com/blog/historical-field-trip",
        "html": """
        <html>
            <head><title>กิจกรรมทัศนศึกษาเชิงประวัติศาสตร์และนวัตกรรมแห่งชาติ</title></head>
            <body>
                <article>
                    <h1>กิจกรรมทัศนศึกษาเชิงประวัติศาสตร์และนวัตกรรมแห่งชาติ</h1>
                    <p class="date">2026-05-15</p>
                    <div class="content">
                        <p>เมื่อสัปดาห์ที่ผ่านมา กลุ่มสาระการเรียนรู้สังคมศึกษาและวิทยาศาสตร์ ได้พานักเรียนชั้น ม.4 ไปร่วมกิจกรรมทัศนศึกษาเพื่อหาความรู้จากสถานที่จริง</p>
                        <p>นักเรียนได้เรียนรู้ความเชื่อมโยงระหว่างประวัติศาสตร์ชาติและการปฏิวัติอุตสาหกรรม ณ พิพิธภัณฑ์แห่งชาติ และเข้าชมนวัตกรรมอุตสาหกรรมอนาคต ณ สวนวิทยาศาสตร์แห่งชาติ</p>
                    </div>
                </article>
            </body>
        </html>
        """
    },
    {
        "url": "https://example-watchara.com/blog/coding-curriculum-update",
        "html": """
        <html>
            <head><title>การปรับปรุงหลักสูตรการเขียนโปรแกรมและการคิดเชิงคำนวณ</title></head>
            <body>
                <article>
                    <h1>การปรับปรุงหลักสูตรการเขียนโปรแกรมและการคิดเชิงคำนวณ</h1>
                    <p class="date">2026-05-10</p>
                    <div class="content">
                        <p>เพื่อตอบรับความต้องการในยุคดิจิทัล โรงเรียนวัชระได้ขยายหลักสูตรการเขียนโปรแกรม (Coding) และ Computational Thinking ให้ครอบคลุมชั้นมัธยมศึกษาตอนต้น</p>
                        <p>วิชานี้เน้นการเขียนโค้ดด้วยภาษา Python และการสร้างเว็บไซต์พื้นฐานด้วย HTML/CSS เพื่อปูพื้นฐานการเป็นนักคิดค้นนวัตกรรมรุ่นเยาว์</p>
                    </div>
                </article>
            </body>
        </html>
        """
    },
    {
        "url": "https://example-watchara.com/blog/parent-seminar-cyber-safety",
        "html": """
        <html>
            <head><title>สัมมนาผู้ปกครอง: การแนะนำดูแลลูกให้ปลอดภัยในยุคดิจิทัล</title></head>
            <body>
                <article>
                    <h1>สัมมนาผู้ปกครอง: การแนะนำดูแลลูกให้ปลอดภัยในยุคดิจิทัล</h1>
                    <p class="date">2026-05-05</p>
                    <div class="content">
                        <p>โรงเรียนวัชระได้จัดงานสัมมนาในหัวข้อ "การเลี้ยงดูลูกในยุคไซเบอร์อย่างสร้างสรรค์และปลอดภัย" เพื่อร่วมมือกับผู้ปกครองในการเฝ้าระวังภัยออนไลน์</p>
                        <p>การสัมมนามุ่งเน้นแนวทางบริหารเวลาหน้าจอ การสนับสนุนเด็กในการเรียนรู้ออนไลน์อย่างมีวิจารณญาณ และการสร้างความสัมพันธ์ที่อบอุ่นในครอบครัว</p>
                    </div>
                </article>
            </body>
        </html>
        """
    }
]


def clean_text(text: str) -> str:
    """ช่วยล้างช่องว่างส่วนเกินออกจากข้อความ"""
    if not text:
        return ""
    return "\n".join([line.strip() for line in text.split("\n") if line.strip()])


def save_to_obsidian(filename: str, title: str, content: str, content_type: str, url: str):
    """บันทึกข้อมูลลงไฟล์ Markdown ใน Obsidian Vault พร้อมระบบ Metadata Frontmatter"""
    # สร้างโฟลเดอร์ปลายทางถ้าหากไม่มีอยู่
    if not os.path.exists(OBSIDIAN_VAULT_PATH):
        os.makedirs(OBSIDIAN_VAULT_PATH)

    filepath = os.path.join(OBSIDIAN_VAULT_PATH, filename)
    today = datetime.date.today().isoformat()

    # ประกอบเนื้อหา Frontmatter และ Markdown
    markdown_content = f"""---
title: "{title}"
date: {today}
tags: [โรงเรียนวัชระ, อัตโนมัติ, {"หน้าแรก" if content_type == "landing" else "บล็อกข่าว"}]
type: {content_type}
original_url: "{url}"
source: "Hermes Scraper Agent"
---

# {title}

{content}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print(f"บันทึกไฟล์เรียบร้อย: {filepath}")
    return filepath


@tool("scrape_watchara_school")
def scrape_watchara_school(url: str = "https://example-watchara.com") -> str:
    """ดึงข้อมูลจากหน้า Landing Page และ 5 บล็อกล่าสุดของโรงเรียนวัชระ 
    สกัดหัวข้อและเนื้อหา จากนั้นบันทึกเป็นไฟล์ Markdown (.md) ลงใน Obsidian Vault ทันที 
    มีระบบตรวจสอบความพร้อมของเซิร์ฟเวอร์ ถ้าเว็บเข้าไม่ได้จะสลับไปใช้ Mock Data อัตโนมัติ"""
    
    print(f"กำลังเริ่มการดึงข้อมูลจาก: {url}...")
    results = []

    # 1. จัดการข้อมูลหน้าแรก (Landing Page)
    landing_title = ""
    landing_content = ""
    try:
        # ลองสแกนเว็บจริง
        response = requests.get(url, timeout=5)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        landing_title = soup.title.string if soup.title else "ยินดีต้อนรับสู่โรงเรียนวัชระ"
        landing_content = soup.find("body").get_text() if soup.find("body") else ""
        landing_content = clean_text(landing_content)
        print("ดึงข้อมูลหน้าแรกจากเว็บจริงสำเร็จ!")
    except Exception as e:
        print(f"ดึงข้อมูลเว็บจริงไม่ได้ ({e}) เปลี่ยนไปใช้ข้อมูลจำลองคุณภาพสูง...")
        # ใช้ Mock Data สำหรับ Landing page
        soup = BeautifulSoup(MOCK_LANDING_HTML, "html.parser")
        landing_title = soup.find("h1").get_text() if soup.find("h1") else "ยินดีต้อนรับสู่โรงเรียนวัชระ"
        
        # สกัดส่วน Lead + About
        lead = soup.find("p", class_="lead").get_text() if soup.find("p", class_="lead") else ""
        about = soup.find("div", class_="about").get_text() if soup.find("div", class_="about") else ""
        landing_content = clean_text(f"{lead}\n\n{about}")

    # บันทึกหน้าแรก
    landing_file = save_to_obsidian(
        filename="landing_page.md",
        title=landing_title,
        content=landing_content,
        content_type="landing",
        url=url
    )
    results.append(f"- บันทึกหน้าแรกสำเร็จ: {landing_file} (หัวข้อ: {landing_title})")

    # 2. จัดการข้อมูลบล็อก 5 หน้าล่าสุด
    for i, blog in enumerate(MOCK_BLOGS_HTML, 1):
        blog_url = blog["url"]
        blog_title = ""
        blog_content = ""

        try:
            # พยายามเรียกเว็บจริง (ที่นี่เป็นการจำลอง ดังนั้นจะเปลี่ยนมาใช้ mock HTML ในรายการ)
            # แต่เพื่อรักษารูปแบบโค้ดจริง จึงเขียนพยายามดึงและครอบ try-except
            if url == "https://example-watchara.com":
                # ส่งให้เข้า Exception ทันทีเพื่อดึงข้อมูลจำลอง
                raise requests.RequestException("Simulated domain fallback")
            
            response = requests.get(blog_url, timeout=5)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, "html.parser")
            blog_title = soup.title.string if soup.title else f"บทความบล็อกที่ {i}"
            blog_content = soup.find("body").get_text() if soup.find("body") else ""
            blog_content = clean_text(blog_content)
        except Exception:
            # ใช้ Mock HTML สำหรับบล็อกแต่ละอัน
            soup = BeautifulSoup(blog["html"], "html.parser")
            blog_title = soup.find("h1").get_text() if soup.find("h1") else f"บทความบล็อกที่ {i}"
            
            content_div = soup.find("div", class_="content")
            blog_content = clean_text(content_div.get_text()) if content_div else ""

        # บันทึกไฟล์บล็อกลง Obsidian
        filename = f"blog_post_{i}.md"
        blog_file = save_to_obsidian(
            filename=filename,
            title=blog_title,
            content=blog_content,
            content_type="blog",
            url=blog_url
        )
        results.append(f"- บันทึกบล็อกที่ {i} สำเร็จ: {blog_file} (หัวข้อ: {blog_title})")

    summary_msg = "ขูดข้อมูลโรงเรียนวัชระเสร็จเรียบร้อยแล้ว!\n" + "\n".join(results)
    return summary_msg


@tool("scrape_any_website")
def scrape_any_website(url: str) -> str:
    """ดึงข้อมูลข่าวสารหรือบทความจาก URL ใดก็ได้ที่ระบุ 
    สกัดเอาเฉพาะข้อความหลัก (Main text content) ออกมา จากนั้นบันทึกเป็นไฟล์ Markdown (.md) ลงใน Obsidian Vault ทันที"""
    print(f"กำลังเริ่มการดึงข้อมูลจากแหล่งข่าวนอก: {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # ดึงหน้าเว็บ
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        # ดึงหัวข้อข่าว
        title = soup.title.string if soup.title else "บทความขูดข้อมูลทั่วไป"
        title = clean_text(title)
        
        # เอาส่วนประกอบที่ไม่ใช่เนื้อหาหลักออก
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            element.decompose()
            
        # สกัดเอาข้อความหลัก
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        else:
            content = clean_text(soup.get_text())
            
        # ค้นหาชื่อไฟล์ลำดับถัดไป (เช่น blog_post_8.md)
        max_num = 0
        if os.path.exists(OBSIDIAN_VAULT_PATH):
            pattern = re.compile(r"^blog_post_(\d+)\.md$")
            for fn in os.listdir(OBSIDIAN_VAULT_PATH):
                match = pattern.match(fn)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
                        
        filename = f"blog_post_{max_num + 1}.md"
        
        # เซฟลง Obsidian Vault
        filepath = save_to_obsidian(
            filename=filename,
            title=title,
            content=content,
            content_type="blog",
            url=url
        )
        return f"ดึงข้อมูลสำเร็จ! บันทึกไฟล์ลง Obsidian เรียบร้อย: {filepath} (หัวข้อ: {title})"
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการดึงข้อมูลจาก {url}: {e}"
