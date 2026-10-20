import streamlit as st
from datetime import datetime
import os
from openai import OpenAI
from storage import load_sessions, save_sessions, image_to_base64

# 1. 页面设置
st.set_page_config(page_title="AI智能伴侣", page_icon="🤖", layout="wide")

# 2. 读取 Key (云端优先，本地回退)
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    api_key = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

# 3. 样式注入
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a1a2e; }
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #FF4B4B !important; color: white !important;
    }
    [data-testid="stChatMessage"] { border-radius: 12px; padding: 8px 16px; }
</style>
""", unsafe_allow_html=True)

# 4. 状态初始化与持久化加载
if "sessions" not in st.session_state:
    saved = load_sessions()
    if saved:
        st.session_state.sessions = saved
        st.session_state.current_session = list(saved.keys())[0]
    else:
        default_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.sessions = {
            default_id: {
                "messages": [],
                "name": "小美",
                "personality": "温柔可爱一口台湾腔的台湾妹子"
            }
        }
        st.session_state.current_session = default_id
        save_sessions(st.session_state.sessions)


# 5. 流式生成器
def stream_ai_response(session, user_input):
    system_prompt = (
        f"你的名字是{session['name']}，"
        f"你的性格是{session['personality']}。"
        f"请严格保持这个人设与用户对话，回复简短自然。"
    )
    messages = [{"role": "system", "content": system_prompt}]
    for msg in session["messages"][-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # 兼容多模态结构
    messages.append({"role": "user", "content": user_input})

    stream = client.chat.completions.create(
        model="deepseek-chat", messages=messages, stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


# 6. 侧边栏
with st.sidebar:
    st.header("AI控制面板")
    if st.button("📝 新建会话", use_container_width=True):
        new_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.sessions[new_id] = {
            "messages": [], "name": "小美", "personality": "温柔可爱一口台湾腔的台湾妹子"
        }
        st.session_state.current_session = new_id
        save_sessions(st.session_state.sessions)
        st.rerun()

    st.subheader("历史会话")
    for sid in list(st.session_state.sessions.keys()):
        col1, col2 = st.columns([4, 1])
        with col1:
            is_active = (sid == st.session_state.current_session)
            if st.button(
                    f"📄 {sid}", key=f"select_{sid}", use_container_width=True,
                    type="primary" if is_active else "secondary"
            ):
                st.session_state.current_session = sid
                st.rerun()
        with col2:
            if st.button("❌", key=f"del_{sid}"):
                del st.session_state.sessions[sid]
                if st.session_state.current_session == sid:
                    if st.session_state.sessions:
                        st.session_state.current_session = list(st.session_state.sessions.keys())[0]
                    else:
                        new_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.session_state.sessions[new_id] = {
                            "messages": [], "name": "小美", "personality": "温柔可爱一口台湾腔的台湾妹子"
                        }
                        st.session_state.current_session = new_id
                save_sessions(st.session_state.sessions)
                st.rerun()

    st.divider()
    current = st.session_state.sessions[st.session_state.current_session]

    st.subheader("名字")
    new_name = st.text_input("名字", value=current["name"], label_visibility="collapsed")
    st.subheader("性格")
    new_personality = st.text_area("性格", value=current["personality"], label_visibility="collapsed")

    if new_name != current["name"] or new_personality != current["personality"]:
        current["name"] = new_name
        current["personality"] = new_personality
        save_sessions(st.session_state.sessions)

    st.divider()
    st.subheader("多模态输入")
    uploaded_image = st.file_uploader("上传图片", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        st.image(uploaded_image, caption="已上传图片", use_container_width=True)

# 7. 主区域渲染
st.title("AI智能伴侣")
st.caption(f"当前会话: {st.session_state.current_session}")

for msg in current["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🤖"):
            if isinstance(msg["content"], list):
                for item in msg["content"]:
                    if item["type"] == "text":
                        st.write(item["text"])
            else:
                st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="😊"):
            st.write(msg["content"])

# 8. 处理新输入
if prompt := st.chat_input("请输入您的问题..."):
    if uploaded_image:
        img_b64 = image_to_base64(uploaded_image)
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]
    else:
        content = prompt

    current["messages"].append({"role": "user", "content": content})

    with st.chat_message("user", avatar="🤖"):
        if uploaded_image:
            st.image(uploaded_image, width=200)
        st.write(prompt)

    with st.chat_message("assistant", avatar="😊"):
        response = st.write_stream(stream_ai_response(current, content))

    current["messages"].append({"role": "assistant", "content": response})
    save_sessions(st.session_state.sessions)