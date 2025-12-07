import streamlit as st
import os  # 新增這個：用來設定系統環境
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# --- 1. 網頁設定 ---
st.set_page_config(page_title="碳權搜尋助理", page_icon="🌿", layout="wide")
st.title("🌿 碳權與碳匯智慧搜尋引擎")

# --- 2. 智慧金鑰管理 ---
# 先預設鑰匙是空的
openai_key = None
tavily_key = None

# A. 嘗試從雲端 (Secrets) 抓取
try:
    if "OPENAI_API_KEY" in st.secrets:
        openai_key = st.secrets["OPENAI_API_KEY"]
    if "TAVILY_API_KEY" in st.secrets:
        tavily_key = st.secrets["TAVILY_API_KEY"]
except:
    pass

# B. 如果雲端沒有 (代表在本機)，就顯示側邊欄讓您輸入
if not openai_key or not tavily_key:
    with st.sidebar:
        st.header("⚙️ 開發者設定")
        openai_key = st.text_input("OpenAI Key", type="password").strip()
        tavily_key = st.text_input("Tavily Key", type="password").strip()
        if not openai_key or not tavily_key:
            st.info("💡 請輸入 Key 以開始測試")

# --- 3. 【關鍵修正】強制寫入環境變數 ---
# 不管鑰匙是從哪裡來的，直接把它們塞進系統環境裡
# 這樣 Tavily 工具就一定找得到，不會再報錯了
if openai_key:
    os.environ["OPENAI_API_KEY"] = openai_key
if tavily_key:
    os.environ["TAVILY_API_KEY"] = tavily_key

# --- 4. 初始化對話紀錄 ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "您好！我是您的碳權顧問。請問想了解什麼？"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- 5. 執行邏輯 ---
if prompt := st.chat_input("請輸入問題..."):
    if not openai_key or not tavily_key:
        st.error("❌ 未偵測到 API Key，請在側邊欄輸入。")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🔍 搜尋與思考中..."):
            try:
                # 1. 設定模型
                llm = ChatOpenAI(model="gpt-4o", temperature=0)
                
                # 2. 設定搜尋工具 (現在不需要傳參數了，它會自己去抓環境變數)
                search = TavilySearchResults()
                tools = [search]

                # 3. 設定指令
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", "你是一位碳權專家，請用繁體中文回答。"),
                    ("user", "{input}"),
                    ("placeholder", "{agent_scratchpad}"),
                ])

                # 4. 執行 Agent
                agent = create_tool_calling_agent(llm, tools, prompt_template)
                agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

                response = agent_executor.invoke({"input": prompt})["output"]
                
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            except Exception as e:
                st.error(f"發生錯誤：{e}")