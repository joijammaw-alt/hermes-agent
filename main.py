import os
import sys
import asyncio
# ป้องกัน UnicodeEncodeError เมื่อพิมพ์ข้อความภาษาไทยหรือ Emoji บน Windows (เช่น cp874)
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

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

# โหลด Environment Variables
load_dotenv()

def check_env():
    """ตรวจสอบความพร้อมของ Environment Variables"""
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        print("=" * 70)
        print("⚠️  [แจ้งเตือน] ไม่พบ ZAI_API_KEY ในไฟล์ .env")
        print("=" * 70)
        return False
    return True

# 1. นำเข้าเครื่องมือที่สร้างไว้ (Custom Tools)
from tools.scraper_tool import scrape_watchara_school
from tools.wp_tool import publish_to_wordpress
from tools.astro_tool import manage_astro_landing_page

def main():
    if not check_env():
        sys.exit(1)

    print("\n🚀 กำลังตั้งค่าระบบและสมองหลักของ Hermes AI Agent...")
    print("🔮 ใช้บริการ Z.ai (GLM 5.1) เป็นสมองหลัก...")
    
    # 2. ตั้งค่า LLM เป็น Z.ai (GLM 5.1)
    llm = LLM(
        model=f"openai/{os.getenv('ZAI_MODEL', 'glm-5.1')}",
        base_url=os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/paas/v4/"),
        temperature=0.2,
        api_key=os.getenv("ZAI_API_KEY")
    )

    # 3. สร้าง Agent "Hermes"
    hermes = Agent(
        role="Full-Stack AI Assistant",
        goal="""ช่วยเหลือนักพัฒนาในการขูดข้อมูลข่าวสารของโรงเรียนวัชระ จัดเก็บข้อมูลลง Obsidian Vault อย่างเป็นระเบียบ, 
เผยแพร่สรุปข่าวที่น่าสนใจลง WordPress REST API, และออกแบบพัฒนาปรับโฉมหน้าแรกเว็บ Astro ด้วย Tailwind CSS ระดับ Premium""",
        backstory="""คุณคือ 'Hermes' สุดยอดผู้ช่วย AI อัจฉริยะแบบ Full-Stack ที่เก่งกาจทั้งด้านวิศวกรรมข้อมูล (Data Scraping) 
การจัดการเนื้อหา (CMS) และการออกแบบพัฒนาเว็บ (Frontend) มีทักษะการดีไซน์ระดับสูงด้วย Tailwind CSS 
คุณทำงานประณีต รอบคอบ ตรวจสอบข้อมูลก่อนโพสต์เสมอ และสื่อสารรายงานผลงานเป็นภาษาไทยที่สุภาพ เรียบร้อย เป็นมืออาชีพ""",
        tools=[scrape_watchara_school, publish_to_wordpress, manage_astro_landing_page],
        llm=llm,
        verbose=True
    )

    # 4. งานที่ 1: ดึงข้อมูลข่าวสารจากเว็บโรงเรียนวัชระและบันทึกลง Obsidian
    task_scrape = Task(
        description="""ใช้เครื่องมือ `scrape_watchara_school` เพื่อดึงข้อมูลหน้าหลัก (Landing Page) 
และบล็อกข่าวสารล่าสุดทั้ง 5 หน้าของโรงเรียนวัชระ (โดยใช้ค่าเริ่มต้นหรือ URL https://example-watchara.com) 
และทำการบันทึกเนื้อหาที่ดึงมาทั้งหมดลงในระบบจัดเก็บเอกสาร Obsidian Vault ในรูปแบบไฟล์ Markdown (.md) แยกตามหัวข้อข่าวอย่างครบถ้วน""",
        expected_output="สรุปรายชื่อไฟล์ข่าวสารทั้งหมดที่บันทึกสำเร็จลงใน Obsidian Vault",
        agent=hermes
    )

    # 5. งานที่ 2: โพสต์ข่าวเด่นลง WordPress (อัปเดตให้โพสต์เพิ่มขึ้น)
    task_wordpress = Task(
        description="""จากบทความทั้งหมดของโรงเรียนวัชระที่ดึงมาในขั้นตอนแรก ให้วิเคราะห์และเลือกข่าวที่น่าสนใจและมีประโยชน์ที่สุดมา 3 ข่าว 
นำข้อมูลทั้ง 3 ข่าวนี้มาเรียบเรียงใหม่เป็นบทความภาษาไทยที่อ่านสนุก จัดรูปแบบเนื้อหาด้วย Tag HTML พื้นฐานอย่างสวยงาม 
จากนั้นให้เรียกใช้เครื่องมือ `publish_to_wordpress` เพื่อเผยแพร่บทความขึ้นระบบเว็บบล็อก (โดยทำการเรียกเครื่องมือนี้แยกกันทีละข่าวจนครบทั้ง 3 ข่าว)""",
        expected_output="ข้อความยืนยันการโพสต์และลิงก์บทความทั้ง 3 ข่าวที่ส่งไปยัง WordPress สำเร็จเรียบร้อย",
        agent=hermes
    )


    # 6. งานที่ 3: ปรับแต่งเว็บ Astro
    task_astro = Task(
        description="""อ่านโครงสร้างเว็บเดิมจากหน้าแรกของ Astro
วิเคราะห์เนื้อหาข้อมูลข่าวสารเด่นทั้งหมดของโรงเรียนวัชระที่ดึงมาในขั้นตอนแรก (นำข่าวสารทั้งหมดที่มีมาคำนวณแสดงผล)
จากนั้น ออกแบบโฉมใหม่หน้าแรกของ Astro โดยนำข่าวสารล่าสุดทั้งหมดมาแสดงผลในรูปแบบ Dynamic Cards Grid ที่รองรับการกรองหมวดหมู่ข่าวอย่างสวยงาม...""",
        expected_output="...",
        agent=hermes
    )


    # 7. ประกอบและจัดตั้ง Crew 
    crew = Crew(
        agents=[hermes],
        tasks=[task_scrape, task_wordpress, task_astro], # รันงานตามลำดับ Sequential ทั้ง 3 งาน
        process=Process.sequential,
        verbose=True
    )

    print("\n🤖 เริ่มต้นการทำงานของ CrewAI - Hermes AI Agent...")
    result = asyncio.run(crew.kickoff_async())
    
    print("\n🎉 Hermes AI Agent Finished Successfully!")
    print(result)

if __name__ == "__main__":
    main()