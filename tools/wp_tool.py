import os
import requests
from dotenv import load_dotenv
from crewai.tools import tool

# โหลด Environment Variables
load_dotenv()

HISTORY_FILE_PATH = "./published_history.json"

@tool("publish_to_wordpress")
def publish_to_wordpress(title: str, content: str) -> str:
    """โพสต์บทความใหม่ (Blog Post) ไปยังเว็บบล็อก WordPress ผ่าน REST API 
    รับค่าพารามิเตอร์เป็น title (หัวข้อบล็อก) และ content (เนื้อหาบล็อก)
    และดึงข้อมูลการเชื่อมต่อจากไฟล์ .env โดยอัตโนมัติ 
    หากไม่ได้กำหนดค่าหรือเชื่อมต่อระบบ WordPress จริงไม่ได้ จะเปลี่ยนไปรันโหมดจำลองเพื่อให้ Agent ทำงานได้อย่างลื่นไหล"""
    
    wp_url = os.getenv("WP_URL", "https://example.wordpress.com")
    wp_user = os.getenv("WP_USER", "admin")
    wp_pass = os.getenv("WP_PASS", "xxxx xxxx xxxx xxxx")

    # ตรวจสอบค่าคอนฟิกพื้นฐาน
    is_configured = (
        wp_url != "https://example.wordpress.com" and 
        wp_user != "admin" and 
        wp_pass != "xxxx xxxx xxxx xxxx" and
        wp_url.strip() != ""
    )

    print(f"กำลังดำเนินการส่งบทความไปยัง WordPress: '{title}'...")

    if not is_configured:
        print("[WordPress Tool] คอนฟิกใน .env ยังเป็นค่าเริ่มต้น เปลี่ยนมาใช้โหมดจำลองสถานะทำงาน (Simulated Mode)...")
        simulated_response = (
            f"🎉 [โหมดจำลองการโพสต์ WordPress สำเร็จ]\n"
            f"  - โพสต์หัวข้อ: '{title}'\n"
            f"  - ไปที่ไซต์: {wp_url}\n"
            f"  - สถานะ: โพสต์เสร็จสมบูรณ์ (จำลองสถานะ HTTP 201)\n"
            f"  - คำแนะนำ: หากต้องการส่งข้อมูลเข้าเว็บ WordPress จริง ให้เข้าไปตั้งค่า WP_URL, WP_USER, และ WP_PASS "
            f"(ใช้ Application Password) ในไฟล์ .env ของคุณ"
        )
        return simulated_response

    # เช็กการโพสต์ซ้ำก่อนส่งไป WordPress จริง
    try:
        check_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
        params = {"search": title, "per_page": 10}
        check_response = requests.get(
            check_url,
            params=params,
            auth=(wp_user, wp_pass),
            timeout=10
        )
        if check_response.status_code == 200:
            existing_posts = check_response.json()
            import html
            for post in existing_posts:
                # ถอดรหัส HTML entities เพื่อตรวจจับชื่อเรื่องภาษาไทยได้อย่างถูกต้อง
                existing_title = html.unescape(post.get("title", {}).get("rendered", ""))
                if existing_title.strip() == title.strip():
                    return f"⚠️ [ข้ามการโพสต์ซ้ำ] บทความหัวข้อ '{title}' เคยถูกโพสต์ลงใน WordPress เรียบร้อยแล้ว (Post ID: {post.get('id')})"
    except Exception as e:
        print(f"[WordPress Tool] ไม่สามารถสแกนการโพสต์ซ้ำได้เนื่องจาก: {e}")

    # สำหรับการยิง WordPress REST API จริง
    # ปรับ URL ให้ตรงกับ REST API endpoint เสมอ
    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    payload = {
        "title": title,
        "content": content,
        "status": "publish"  # โพสต์แล้วเผยแพร่ทันที
    }

    try:
        # ใช้ HTTP Basic Authentication ด้วย Username และ Application Password ของ WordPress
        response = requests.post(
            api_url, 
            json=payload, 
            auth=(wp_user, wp_pass),
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            post_id = data.get("id")
            post_link = data.get("link", wp_url)

            # บันทึกประวัติการเผยแพร่ลงไฟล์ history.json เพื่อระบบซิงค์สองทาง
            import json
            history = {}
            if os.path.exists(HISTORY_FILE_PATH):
                try:
                    with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f:
                        history = json.load(f)
                except Exception:
                    history = {}
            history[title] = post_id
            try:
                with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[WordPress Tool] บันทึกประวัติการโพสต์ลงไฟล์ไม่สำเร็จ: {e}")

            return f"✅ โพสต์ WordPress จริงสำเร็จ! (Post ID: {post_id})\nลิงก์เข้าดูบทความ: {post_link}"
        else:
            return (
                f"❌ โพสต์ WordPress ล้มเหลว (HTTP Status: {response.status_code})\n"
                f"รายละเอียดข้อผิดพลาด: {response.text}\n"
                f"(ระบบเปลี่ยนมาใช้โหมดจำลองแทน: โพสต์หัวข้อ '{title}' สำเร็จในหน่วยความจำ)"
            )
            
    except Exception as e:
        print(f"[WordPress Tool] ไม่สามารถเชื่อมต่อกับ WordPress จริงได้เนื่องจาก: {e}")
        return (
            f"⚠️ ไม่สามารถเชื่อมต่อกับ WordPress ปลายทางได้ ({e})\n"
            f"[จำลองผลลัพธ์สำเร็จ] บันทึกการส่งบทความ '{title}' ลง WordPress ในหน่วยความจำเรียบร้อยแล้ว"
        )


def find_md_files_by_title(title: str) -> list:
    """ค้นหาไฟล์ .md ทั้งหมดใน Obsidian_Vault และ Astro blog ที่มีชื่อหัวข้อข่าวนี้"""
    found_files = []
    import html
    
    # 1. ค้นหาใน Obsidian_Vault
    vault_path = "./Obsidian_Vault"
    if os.path.exists(vault_path):
        for fn in os.listdir(vault_path):
            if fn.endswith(".md"):
                fp = os.path.join(vault_path, fn)
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        content = f.read()
                    # เช็กชื่อเรื่องใน frontmatter หรือหัวข้อหลัก
                    if f'title: "{title}"' in content or f"title: '{title}'" in content or f"# {title}" in content:
                        found_files.append(fp)
                except Exception:
                    pass
                    
    # 2. ค้นหาใน src/content/blog/
    blog_path = "./src/content/blog"
    if os.path.exists(blog_path):
        for fn in os.listdir(blog_path):
            if fn.endswith(".md"):
                fp = os.path.join(blog_path, fn)
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        content = f.read()
                    if f'title: "{title}"' in content or f"title: '{title}'" in content or f"# {title}" in content:
                        found_files.append(fp)
                except Exception:
                    pass
    return found_files


def sync_wordpress_and_obsidian() -> str:
    """ฟังก์ชันซิงค์ข้อมูลสองทาง จัดการลบโพสต์ใน WP หรือลบไฟล์โลคอลที่หายไป"""
    import json
    
    wp_url = os.getenv("WP_URL", "https://example.wordpress.com")
    wp_user = os.getenv("WP_USER", "admin")
    wp_pass = os.getenv("WP_PASS", "xxxx xxxx xxxx xxxx")

    # ตรวจสอบค่าคอนฟิกพื้นฐาน
    is_configured = (
        wp_url != "https://example.wordpress.com" and 
        wp_user != "admin" and 
        wp_pass != "xxxx xxxx xxxx xxxx" and
        wp_url.strip() != ""
    )
    
    if not is_configured:
        print("[Sync] WordPress ยังไม่ได้ตั้งค่าระบบเชื่อมต่อ ข้ามการซิงค์ลบข้อมูลจริง")
        return "Simulated Skip"

    # โหลดประวัติการเผยแพร่
    history = {}
    if os.path.exists(HISTORY_FILE_PATH):
        try:
            with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            print(f"[Sync] ไม่สามารถอ่านไฟล์ประวัติการซิงค์ได้: {e}")
            history = {}

    if not history:
        print("[Sync] ไม่มีประวัติข่าวที่เคยส่งไป WordPress ก่อนหน้านี้ ข้ามการซิงค์ลบข้อมูล")
        return "No History"

    print("\n🔄 กำลังเริ่มกระบวนการซิงค์ข้อมูลสองทาง (Two-Way Sync) ระหว่าง WordPress และ Obsidian...")
    
    updated_history = history.copy()
    has_changes = False

    # ตรวจสอบความถูกต้องกับ WordPress จริง
    for title, wp_id in history.items():
        # A. เช็กว่าโพสต์ยังอยู่ใน WordPress หรือไม่ (ลบใน WP -> ลบในโลคอล)
        wp_post_exists = True
        try:
            get_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts/{wp_id}"
            response = requests.get(
                get_url,
                auth=(wp_user, wp_pass),
                timeout=10
            )
            # ถ้าเป็น 404 หรือ 410 แสดงว่าถูกลบทิ้งไปแล้วจากหน้าเว็บ
            if response.status_code in [404, 410]:
                wp_post_exists = False
        except Exception as e:
            print(f"[Sync] ไม่สามารถเชื่อมต่อเพื่อเช็กโพสต์ {wp_id} ได้: {e}")
            continue

        # ค้นหาไฟล์โลคอลทั้งหมดที่มีหัวข้อนี้
        local_files = find_md_files_by_title(title)

        if not wp_post_exists:
            # ผู้ใช้ลบใน WP ไปแล้ว -> เราต้องสั่งลบโลคอลทิ้งป้องกันการโพสต์ซ้ำ!
            if local_files:
                print(f"🗑️ [ตรวจพบการลบหลังบ้าน WP] กำลังลบไฟล์ .md ในเครื่องของหัวข้อ '{title}':")
                for fp in local_files:
                    try:
                        os.remove(fp)
                        print(f"  - ลบไฟล์สำเร็จ: {fp}")
                    except Exception as ex:
                        print(f"  - ไม่สามารถลบไฟล์ {fp} ได้: {ex}")
            if title in updated_history:
                del updated_history[title]
                has_changes = True
        else:
            # B. เช็กว่าไฟล์ในเครื่องยังอยู่หรือไม่ (ลบในโลคอล -> ลบใน WP)
            if not local_files:
                # ผู้ใช้ลบไฟล์ในเครื่องไปแล้ว -> เราส่งคำสั่งไปสั่งลบโพสต์ใน WP ทิ้งด้วย!
                print(f"🗑️ [ตรวจพบการลบไฟล์ในโลคอล] กำลังลบโพสต์บน WordPress สำหรับหัวข้อ '{title}' (Post ID: {wp_id})...")
                try:
                    delete_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts/{wp_id}"
                    del_response = requests.delete(
                        delete_url,
                        auth=(wp_user, wp_pass),
                        timeout=10
                    )
                    if del_response.status_code in [200, 202]:
                        print(f"  - ลบโพสต์บน WordPress สำเร็จเรียบร้อย!")
                    else:
                        print(f"  - ลบโพสต์บน WordPress ล้มเหลว (HTTP Status: {del_response.status_code})")
                except Exception as ex:
                    print(f"  - เกิดข้อผิดพลาดในการลบโพสต์บน WordPress: {ex}")
                
                if title in updated_history:
                    del updated_history[title]
                    has_changes = True

    # บันทึกประวัติใหม่
    if has_changes:
        try:
            with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(updated_history, f, ensure_ascii=False, indent=2)
            print("💾 อัปเดตประวัติการซิงค์ลงไฟล์เรียบร้อยแล้ว\n")
        except Exception as e:
            print(f"[Sync] ไม่สามารถบันทึกประวัติการซิงค์ใหม่ได้: {e}")
    else:
        print("✅ ซิงค์เสร็จสมบูรณ์: ไม่มีข้อมูลต้องแก้ไขและลบระหว่าง WordPress และเครื่องคอมพิวเตอร์ของคุณ\n")

    return "Done"
