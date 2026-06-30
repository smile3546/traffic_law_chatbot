import os
import re
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# 載入環境變數並設定 API Key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ==========================================
# 1. 頁面配置與 UI 設定
# ==========================================
st.set_page_config(
    page_title="交通法規與肇責諮詢系統", 
    page_icon="🚗",
    layout="centered"
)

st.title("🚗 交通法規與肇責諮詢系統")

# ==========================================
# 2. 資料載入機制
# ==========================================
@st.cache_resource
def load_law_knowledge():
    data_path = "data/traffic_law.txt"
    if not os.path.exists(data_path):
        st.error(f"【系統錯誤】找不到知識庫檔案，請確認路徑是否存在：{data_path}")
        st.stop()
        
    with open(data_path, "r", encoding="utf-8") as f:
        return f.read()

knowledge_base = load_law_knowledge()

# ==========================================
# 3. 定義 System Prompt
# ==========================================
system_prompt = f"""您是一位精通中華民國交通法規與產險公會理賠實務的專家。
請直接、嚴謹地根據下方【交通知識庫】內容回答使用者。

應答規範：
1. 涉及裁罰金額、記點點數或肇事責任分攤比例，必須完全依據知識庫內容回答。
2. 若遇到複合型違規（如主因車同時有超速等），請啟用知識庫中的「產險公會肇責增減扣抵公式」，並列出清晰的計算過程。
3. 請以條理清晰的 Markdown 排版輸出，語氣流暢流利、嚴謹直接，不帶贅字與任何不必要的客套。
4. 每則回覆的最後一行，請附上標準的理賠與法律免責聲明。

【交通知識庫】
{knowledge_base}
"""

# ==========================================
# 4. 初始化 Gemini 3.1 核心模型
# ==========================================
model = genai.GenerativeModel(
    model_name="gemini-3.1-flash-lite",
    generation_config={"temperature": 0.3}
)

# ==========================================
# 5. 對話紀錄狀態管理
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "請輸入您欲查詢的違規裁罰情境、路權判定或特定車禍肇責比例計算："
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 6. 即時對話處理管線
# ==========================================
if user_query := st.chat_input("請描述您的情境..."):
    
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
        
    with st.chat_message("assistant"):
        with st.spinner("系統檢索中..."):
            
            full_prompt = f"{system_prompt}\n\n【使用者當前諮詢情境】\n{user_query}\n\n專家答覆："
            
            try:
                response = model.generate_content(full_prompt)
                raw_text = response.text
                
                # 移除任何可能出面的 標籤
                clean_text = re.sub(r'\[\s*cite:[^\]]+\]', '', raw_text)
                
                st.markdown(clean_text)
                st.session_state.messages.append({"role": "assistant", "content": clean_text})
                
            except Exception as e:
                st.error(f"【API 呼叫異常】錯誤訊息：{str(e)}")