import os
import requests
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อม
load_dotenv()

wp_url = os.getenv("WP_URL")
wp_user = os.getenv("WP_USER")
wp_pass = os.getenv("WP_PASS")

api_url = wp_url.rstrip("/") + "/wp-json/wp/v2/posts"

payload = {
    "title": "โรงเรียนวัชระ ก้าวล้ำนำสมัย เปิดห้องเรียน AI และหุ่นยนต์แห่งอนาคต!",
    "content": """
    <p><strong>โรงเรียนวัชระ ก้าวล้ำนำสมัย เปิดห้องเรียน AI และหุ่นยนต์แห่งอนาคต!</strong></p>
    <p>โรงเรียนวัชระมีความภูมิใจที่จะประกาศถึงความสำเร็จครั้งสำคัญในการเปิดตัว "ห้องเรียน AI และหุ่นยนต์" อย่างเป็นทางการ ซึ่งถือเป็นก้าวสำคัญในการยกระดับการศึกษาไทยให้ก้าวทันเทคโนโลยีระดับโลก</p>
    <p>ห้องเรียนแห่งอนาคตนี้ ได้รับการออกแบบมาเพื่อ:</p>
    <ul>
      <li><strong>ส่งเสริมทักษะแห่งศตวรรษที่ 21:</strong> นักเรียนจะได้เรียนรู้และลงมือปฏิบัติจริงกับเทคโนโลยีปัญญาประดิษฐ์ (AI) และหุ่นยนต์</li>
      <li><strong>สร้างนักนวัตกรรมรุ่นเยาว์:</strong> ปลูกฝังกระบวนการคิดเชิงวิพากษ์ การแก้ปัญหา และความคิดสร้างสรรค์</li>
      <li><strong>เตรียมความพร้อมสู่อาชีพแห่งอนาคต:</strong> เปิดโอกาสให้นักเรียนได้สัมผัสกับเทคโนโลยีที่จะเป็นรากฐานสำคัญของอุตสาหกรรมในอนาคต</li>
    </ul>
    <p>การเปิดห้องเรียน AI และหุ่นยนต์ในครั้งนี้ สะท้อนให้เห็นถึงความมุ่งมั่นของโรงเรียนวัชระในการมอบการศึกษาที่มีคุณภาพสูงสุด และเตรียมความพร้อมให้นักเรียนทุกคนเป็นกำลังสำคัญในการขับเคลื่อนสังคมและประเทศชาติต่อไป</p>
    """,
    "status": "publish"
}

print(f"กำลังดำเนินการส่งบทความไปยัง WordPress: {wp_url}...")

try:
    res = requests.post(api_url, json=payload, auth=(wp_user, wp_pass), timeout=10)
    print("STATUS CODE:", res.status_code)
    if res.status_code == 201:
        data = res.json()
        print("SUCCESS! Post ID:", data.get("id"))
        print("LINK:", data.get("link"))
    else:
        print("ERROR RESPONSE:", res.text)
except Exception as e:
    print("CONNECTION ERROR:", e)
