import os
from crewai.tools import tool

ASTRO_FILE_PATH = "./src/pages/index.astro"

DEFAULT_ASTRO_CONTENT = """---
// index.astro - หน้าหลักแบบเดิมของโรงเรียนวัชระ (เรียบง่ายและดีไซน์ดั้งเดิม)
---
<html lang="th">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>โรงเรียนวัชระ</title>
</head>
<body style="font-family: sans-serif; padding: 20px; background-color: #f0f0f0;">
    <h1 style="color: #333;">ยินดีต้อนรับสู่โรงเรียนวัชระ</h1>
    <p>เว็บไซต์แสดงข้อมูลข่าวสารประชาสัมพันธ์และวิชาเรียนของโรงเรียน</p>
    
    <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 5px;">
        <h2>ข่าวประกาศล่าสุด</h2>
        <p>ยังไม่มีการอัปเดตข้อมูลข่าวประชาสัมพันธ์ใหม่ล่าสุดในระบบ...</p>
    </div>
</body>
</html>
"""


@tool("manage_astro_landing_page")
def manage_astro_landing_page(action: str, content: str = "") -> str:
    """เครื่องมือจัดการไฟล์หน้าแรกของเว็บ Astro (src/pages/index.astro) 
    ใช้ในการจำลองการทำงานของนักพัฒนาเว็บ โดยสนับสนุนสองการทำงานหลัก:
    1. action="read": อ่านโค้ดโครงสร้างเว็บ Astro ปัจจุบัน (หากไม่มีไฟล์ระบบจะสร้างไฟล์ดีไซน์ดั้งเดิมเริ่มต้นให้ทันที)
    2. action="write": อัปเดต/เขียนโค้ดหน้าเว็บ Astro ใหม่ที่มีการนำเสนอดีไซน์ระดับ Premium ด้วย Tailwind CSS
    
    พารามิเตอร์:
    - action: คำสั่งในการจัดการไฟล์ ("read" หรือ "write")
    - content: โค้ดหน้าเว็บ Astro ใหม่ทั้งหมด (ต้องระบุหาก action="write")"""
    
    # ตรวจสอบและสร้างโฟลเดอร์ปลายทางหากยังไม่มี
    dir_name = os.path.dirname(ASTRO_FILE_PATH)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)

    if action == "read":
        print(f"[Astro Tool] กำลังดำเนินการอ่านไฟล์: {ASTRO_FILE_PATH}...")
        if not os.path.exists(ASTRO_FILE_PATH):
            print(f"[Astro Tool] ไม่พบไฟล์เดิม สร้างไฟล์โครงสร้างดั้งเดิมเริ่มต้นที่: {ASTRO_FILE_PATH}")
            with open(ASTRO_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(DEFAULT_ASTRO_CONTENT)
            return DEFAULT_ASTRO_CONTENT
        
        with open(ASTRO_FILE_PATH, "r", encoding="utf-8") as f:
            current_code = f.read()
        return current_code

    elif action == "write":
        print(f"[Astro Tool] กำลังดำเนินการเขียนโค้ดใหม่ลงไฟล์: {ASTRO_FILE_PATH}...")
        if not content or content.strip() == "":
            return "❌ ผิดพลาด: ไม่สามารถเขียนข้อมูลว่างเปล่าลงในไฟล์ได้ กรุณาระบุพารามิเตอร์ 'content'"
        
        with open(ASTRO_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        
        success_msg = (
            f"✅ ทำการเขียนไฟล์หน้าแรกเว็บสำเร็จเรียบร้อยที่: {ASTRO_FILE_PATH}\n"
            f"ขนาดไฟล์: {len(content)} ตัวอักษร\n"
            f"รายละเอียด: โค้ดได้รับการปรับปรุงให้แสดงผลสวยงามและทันสมัยด้วย Tailwind CSS พร้อมนำเนื้อหาจากโรงเรียนวัชระมาจัดแสดงแบบไดนามิกเรียบร้อยแล้ว!"
        )
        return success_msg

    else:
        return f"❌ ข้อผิดพลาด: ไม่รู้จักคำสั่ง action='{action}' (คำสั่งที่ระบบอนุญาตคือ 'read' หรือ 'write' เท่านั้น)"
