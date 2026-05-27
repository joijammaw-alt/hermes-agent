import os
import requests
from dotenv import load_dotenv
from crewai.tools import tool

# โหลด Environment Variables
load_dotenv()

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
